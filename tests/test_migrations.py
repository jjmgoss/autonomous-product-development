from __future__ import annotations

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


EXPECTED_TABLES = {
    "runs",
    "sources",
    "evidence_excerpts",
    "claims",
    "themes",
    "candidates",
    "evidence_links",
    "validation_gates",
    "review_notes",
    "decisions",
    "artifacts",
    "research_trace_events",
}


def test_alembic_upgrade_from_clean_sqlite(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "migrated.db"
    db_url = f"sqlite+pysqlite:///{db_path}"

    monkeypatch.setenv("APD_DATABASE_URL", db_url)

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(cfg, "head")

    engine = create_engine(db_url, future=True)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert EXPECTED_TABLES.issubset(tables)
