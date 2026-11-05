"""Extraction des offres depuis l'API publique Remotive (sans clé) + contrat de données.

Chaque offre est validée avec Pydantic avant d'entrer dans le pipeline :
les offres invalides sont comptées et écartées, jamais chargées silencieusement.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import requests
from pydantic import BaseModel, Field, ValidationError

log = logging.getLogger(__name__)

SOURCE = "remotive"
API_URL = "https://remotive.com/api/remote-jobs"
# src/jobmarket/extract.py -> racine du projet (ou /opt/airflow dans Docker)
SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_jobs.json"


class JobPosting(BaseModel):
    """Contrat de données d'une offre d'emploi."""

    id: int
    url: str
    title: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    category: str | None = None
    job_type: str | None = None
    publication_date: datetime
    candidate_required_location: str | None = None
    salary: str | None = None
    description: str | None = None


def fetch_jobs(
    category: str,
    *,
    limit: int | None = None,
    timeout: int = 30,
    session: requests.Session | None = None,
) -> list[dict]:
    """Appelle l'API Remotive pour une catégorie et renvoie les offres brutes."""
    http = session or requests
    params: dict[str, str | int] = {"category": category}
    if limit:
        params["limit"] = limit
    response = http.get(
        API_URL,
        params=params,
        timeout=timeout,
        headers={"User-Agent": "job-market-intelligence/0.1"},
    )
    response.raise_for_status()
    jobs = response.json().get("jobs", [])
    log.info("Remotive[%s] : %d offres reçues", category, len(jobs))
    return jobs


def load_sample(path: Path = SAMPLE_PATH) -> list[dict]:
    """Charge le jeu de données d'exemple (démo hors-ligne et tests)."""
    return json.loads(path.read_text(encoding="utf-8"))["jobs"]


def validate_jobs(raw_jobs: list[dict]) -> tuple[list[dict], int]:
    """Valide les offres. Renvoie (offres valides normalisées, nombre rejeté)."""
    valid: list[dict] = []
    rejected = 0
    for raw in raw_jobs:
        try:
            job = JobPosting.model_validate(raw)
        except ValidationError as exc:
            rejected += 1
            log.warning("Offre rejetée (id=%s) : %s", raw.get("id"), exc.errors()[0]["msg"])
            continue
        valid.append(job.model_dump(mode="json"))
    return valid, rejected


def extract(
    categories: list[str],
    *,
    use_sample: bool = False,
    limit: int | None = None,
) -> tuple[list[dict], int]:
    """Extrait puis valide les offres. Renvoie (offres valides dédupliquées, nb rejetées)."""
    if use_sample:
        raw_jobs = load_sample()
    else:
        raw_jobs = []
        for category in categories:
            raw_jobs.extend(fetch_jobs(category, limit=limit))

    valid, rejected = validate_jobs(raw_jobs)
    unique = {job["id"]: job for job in valid}  # une offre peut figurer dans 2 catégories
    return list(unique.values()), rejected
