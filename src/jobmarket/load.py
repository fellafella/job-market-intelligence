"""Chargement : fichier brut (data lake local) + table raw.jobs_raw dans PostgreSQL."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

import psycopg2
from psycopg2.extras import Json, execute_values

from jobmarket.config import Settings

log = logging.getLogger(__name__)

DDL = """
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.jobs_raw (
    source         text        NOT NULL,
    job_id         text        NOT NULL,
    extracted_date date        NOT NULL,
    extracted_at   timestamptz NOT NULL DEFAULT now(),
    payload        jsonb       NOT NULL,
    PRIMARY KEY (source, job_id, extracted_date)
);
"""


def get_connection(settings: Settings):
    return psycopg2.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.dbname,
        user=settings.user,
        password=settings.password,
    )


def ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()


def save_raw_file(jobs: list[dict], run_date: date, raw_dir: Path) -> Path:
    """Écrit un instantané JSON horodaté : la zone "raw" immuable du data lake local."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"jobs_{run_date.isoformat()}.json"
    path.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_raw(conn, jobs: list[dict], *, source: str, extracted_date: date) -> int:
    """Insère les offres dans raw.jobs_raw. Idempotent : relancer le même jour n'ajoute rien.

    Renvoie le nombre de lignes réellement insérées.
    """
    if not jobs:
        return 0
    rows = [(source, str(job["id"]), extracted_date, Json(job)) for job in jobs]
    sql = """
        INSERT INTO raw.jobs_raw (source, job_id, extracted_date, payload)
        VALUES %s
        ON CONFLICT (source, job_id, extracted_date) DO NOTHING
        RETURNING job_id
    """
    with conn.cursor() as cur:
        inserted = execute_values(cur, sql, rows, page_size=500, fetch=True)
    conn.commit()
    return len(inserted)
