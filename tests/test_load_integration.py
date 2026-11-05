"""Test d'intégration : s'exécute seulement si une base PostgreSQL est joignable
(variable WAREHOUSE_HOST définie, par exemple dans la CI)."""

import os
from datetime import date

import pytest

from jobmarket.config import get_settings
from jobmarket.extract import load_sample, validate_jobs
from jobmarket.load import ensure_schema, get_connection, load_raw

pytestmark = pytest.mark.skipif(
    not os.getenv("WAREHOUSE_HOST"), reason="WAREHOUSE_HOST non défini : pas de base de test"
)


@pytest.fixture
def conn():
    connection = get_connection(get_settings())
    ensure_schema(connection)
    yield connection
    with connection.cursor() as cur:
        cur.execute("DELETE FROM raw.jobs_raw WHERE source = 'pytest'")
    connection.commit()
    connection.close()


def test_load_is_idempotent(conn):
    jobs, _ = validate_jobs(load_sample())
    day = date(2026, 11, 4)

    first = load_raw(conn, jobs, source="pytest", extracted_date=day)
    second = load_raw(conn, jobs, source="pytest", extracted_date=day)

    assert first == 10
    assert second == 0  # relancer le même jour n'ajoute aucun doublon
