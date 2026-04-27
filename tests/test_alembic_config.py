from pathlib import Path

from alembic.config import Config


def test_alembic_config_is_sane() -> None:
    cfg = Config("alembic.ini")

    assert cfg.get_main_option("script_location") == "alembic"
    assert cfg.get_main_option("sqlalchemy.url").startswith("sqlite")
    assert Path("alembic/env.py").is_file()
    assert Path("alembic/versions").is_dir()
