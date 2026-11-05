FROM apache/airflow:2.10.5-python3.11

USER airflow

# dbt est installé dans un environnement virtuel dédié pour éviter
# tout conflit de dépendances avec Airflow.
# dbt-core est fixé explicitement : dbt-postgres n'a pas de borne haute et pip
# installerait sinon dbt-core 2.0 (alpha), qui ne supporte pas PostgreSQL.
RUN python -m venv /home/airflow/dbt_venv \
    && /home/airflow/dbt_venv/bin/pip install --no-cache-dir \
        "dbt-core~=1.8.0" "dbt-postgres~=1.8.0" \
    && /home/airflow/dbt_venv/bin/dbt --version

# requests, pydantic et psycopg2 sont déjà fournis par l'image Airflow.
COPY --chown=airflow:root start.sh /opt/airflow/start.sh

CMD ["bash", "/opt/airflow/start.sh"]