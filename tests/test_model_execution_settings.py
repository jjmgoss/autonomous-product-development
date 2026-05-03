from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apd.app.db import Base
from apd.services.model_execution_settings import save_model_execution_settings, get_model_execution_settings
from apd.domain.models import AppSetting


def test_save_and_load_model_execution_settings(tmp_path):
    db_path = tmp_path / "test_settings.db"
    db_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(db_url, future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with Session() as s:
        data = {
            "provider": "ollama",
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "test-model",
            "ollama_timeout_seconds": 99,
            "ollama_keep_alive": 5,
            "component_repair_attempts": 2,
            "research_search_provider": "brave",
            "brave_search_base_url": "https://api.search.brave.com/res/v1/web/search",
            "enabled": True,
        }
        save_model_execution_settings(s, data)
        s.commit()

        # Verify persisted
        row = s.query(AppSetting).filter(AppSetting.key == "model_execution_settings").first()
        assert row is not None
        assert row.value_json["ollama_model"] == "test-model"

        loaded = get_model_execution_settings(s)
        assert loaded["ollama_model"] == "test-model"
        assert loaded["ollama_base_url"] == "http://localhost:11434"
        assert loaded["research_search_provider"] == "brave"
        assert loaded["brave_search_base_url"] == "https://api.search.brave.com/res/v1/web/search"
