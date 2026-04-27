from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from apd.app.db import Base
from apd.fixtures.seed import seed_fixture_data


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test_ui.db"
    db_url = f"sqlite+pysqlite:///{db_path}"

    from sqlalchemy.orm import sessionmaker
    from fastapi.staticfiles import StaticFiles

    test_engine = create_engine(db_url, future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    with TestSession() as session:
        seed_fixture_data(session)
        session.commit()

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

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()


def test_candidates_render_before_sources(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    body = resp.text
    idx_cand = body.find("Candidates")
    idx_sources = body.find("Sources")
    assert idx_cand != -1 and idx_sources != -1
    assert idx_cand < idx_sources


def test_candidate_card_includes_title_and_linked_gate(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    body = resp.text
    assert "Release Guardrails Assistant" in body
    assert "Confirm willingness to pay" in body
