#!/usr/bin/env bash
set -euo pipefail

airflow db migrate

airflow users create \
  --username "${AIRFLOW_USER:-admin}" \
  --password "${AIRFLOW_PASSWORD:-admin}" \
  --firstname Admin --lastname User \
  --role Admin --email admin@example.com || true

airflow scheduler &
exec airflow webserver --port 8080
