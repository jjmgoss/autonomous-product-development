"""Tests for website-first stub research execution (issue #44).
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest

from apd.app.db import Base
from apd.services.research_brief_service import create_brief, get_brief
from apd.services.research_execution_stub import execute_research_brief_stub


@pytest.fixture()
def db(tmp_path):
    db_path = tmp_path / "test_exec.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with Session() as session:
        yield session


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test_briefs_web.db"
    db_url = f"sqlite+pysqlite:///{db_path}"

    test_engine = create_engine(
        db_url,
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False, future=True
    )

    import apd.web.routes as web_routes
    import apd.app.db as app_db

    monkeypatch.setattr(app_db, "engine", test_engine)
    monkeypatch.setattr(app_db, "SessionLocal", TestSession)

    def _override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    from apd.app.main import app

    app.dependency_overrides[web_routes._get_db] = _override_get_db

    from fastapi.testclient import TestClient

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()


def test_execute_stub_service_imports_run(db):
    brief = create_brief(db, title="Stub brief", research_question="Q")
    # reload brief from DB
    brief = get_brief(db, brief.id)
    result = execute_research_brief_stub(db, brief)
    assert result.get("success") is True
    assert isinstance(result.get("run_id"), int)


def test_start_research_route_creates_run(client):
    # create brief via web route then start research
    resp = client.post("/briefs", data={"title": "Web stub", "research_question": "What is X?"}, follow_redirects=False)
    assert resp.status_code == 303
    location = resp.headers["location"]
    # get brief id from redirect
    assert location.startswith("/briefs/")
    brief_id = int(location.split("/")[-1])

    # invoke start research
    resp2 = client.post(f"/briefs/{brief_id}/start-research", follow_redirects=True)
    assert resp2.status_code == 200
    # Should redirect to run detail and show the run title
    assert "Web stub" in resp2.text


