"""Configuration lue depuis les variables d'environnement."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    raw_dir: Path
    categories: list[str]


def get_settings() -> Settings:
    categories = os.getenv("JOBS_CATEGORIES", "data")
    return Settings(
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_PORT", "5432")),
        dbname=os.getenv("WAREHOUSE_DB", "warehouse"),
        user=os.getenv("WAREHOUSE_USER", "jobs"),
        password=os.getenv("WAREHOUSE_PASSWORD", "jobs"),
        raw_dir=Path(os.getenv("RAW_DATA_DIR", "data/raw")),
        categories=[c.strip() for c in categories.split(",") if c.strip()],
    )
