from apd.app.db import Base, engine
from apd.app.settings import get_settings


def test_default_database_url_is_sqlite() -> None:
    settings = get_settings()
    assert settings.database_url.startswith("sqlite+pysqlite:///")


def test_sqlalchemy_engine_and_metadata_exist() -> None:
    assert engine is not None
    assert Base.metadata is not None
