from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


DEFAULT_DB_PATH = Path(".local") / "apd.db"


@dataclass(frozen=True)
class Settings:
    database_url: str


def get_settings() -> Settings:
    db_url = os.getenv("APD_DATABASE_URL")
    if db_url:
        return Settings(database_url=db_url)
    return Settings(database_url=f"sqlite+pysqlite:///{DEFAULT_DB_PATH}")
