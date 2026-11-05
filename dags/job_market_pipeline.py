"""DAG quotidien : extraction API -> chargement raw -> dbt seed -> dbt run -> dbt test."""

from __future__ import annotations

import os
from datetime import date, timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# dbt vit dans un venv séparé (voir docker/airflow/Dockerfile)
DBT = "/home/airflow/dbt_venv/bin/dbt"
DBT_ARGS = "--project-dir $DBT_PROJECT_DIR --profiles-dir $DBT_PROFILES_DIR"


def _extract_and_load(ds: str, **_) -> dict:
    # Import local : garde le parsing du DAG rapide
    from jobmarket.pipeline import run

    use_sample = os.getenv("USE_SAMPLE_DATA", "false").lower() == "true"
    return run(date.fromisoformat(ds), use_sample=use_sample)


with DAG(
    dag_id="job_market_pipeline",
    description="ELT quotidien des offres d'emploi data (Remotive -> PostgreSQL -> dbt)",
    schedule="@daily",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "data-eng", "retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["elt", "dbt", "jobs"],
) as dag:
    extract_and_load = PythonOperator(
        task_id="extract_and_load",
        python_callable=_extract_and_load,
    )

    dbt_seed = BashOperator(task_id="dbt_seed", bash_command=f"{DBT} seed {DBT_ARGS}")
    dbt_run = BashOperator(task_id="dbt_run", bash_command=f"{DBT} run {DBT_ARGS}")
    dbt_test = BashOperator(task_id="dbt_test", bash_command=f"{DBT} test {DBT_ARGS}")

    extract_and_load >> dbt_seed >> dbt_run >> dbt_test
