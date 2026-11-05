"""Orchestration Python du flux extraction -> validation -> chargement.

Utilisable seul :  python -m jobmarket.pipeline --sample
Appelé par Airflow : voir dags/job_market_pipeline.py
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date

from jobmarket.config import get_settings
from jobmarket.extract import SOURCE, extract
from jobmarket.load import ensure_schema, get_connection, load_raw, save_raw_file

log = logging.getLogger(__name__)


def run(
    run_date: date | None = None,
    *,
    use_sample: bool = False,
    limit: int | None = None,
) -> dict:
    """Exécute le flux complet et renvoie des statistiques (sérialisables en JSON)."""
    settings = get_settings()
    run_date = run_date or date.today()

    jobs, rejected = extract(settings.categories, use_sample=use_sample, limit=limit)
    raw_file = save_raw_file(jobs, run_date, settings.raw_dir)

    conn = get_connection(settings)
    try:
        ensure_schema(conn)
        inserted = load_raw(conn, jobs, source=SOURCE, extracted_date=run_date)
    finally:
        conn.close()

    stats = {
        "run_date": run_date.isoformat(),
        "extracted": len(jobs),
        "rejected": rejected,
        "inserted": inserted,
        "raw_file": str(raw_file),
    }
    log.info("Pipeline terminé : %s", stats)
    return stats


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ingestion des offres d'emploi data")
    parser.add_argument("--sample", action="store_true", help="utilise data/sample_jobs.json")
    parser.add_argument("--limit", type=int, default=None, help="nombre max d'offres par catégorie")
    parser.add_argument("--date", type=date.fromisoformat, default=None, help="AAAA-MM-JJ")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(json.dumps(run(args.date, use_sample=args.sample, limit=args.limit), indent=2))


if __name__ == "__main__":
    main()
