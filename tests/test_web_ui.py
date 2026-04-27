from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from apd.app.db import Base
from apd.fixtures.seed import seed_fixture_data


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Return a TestClient wired to an isolated in-memory-style SQLite DB with fixture data."""
    db_path = tmp_path / "test_ui.db"
    db_url = f"sqlite+pysqlite:///{db_path}"

    # Patch the engine and SessionLocal in the modules that use them
    from sqlalchemy.orm import sessionmaker
    from fastapi.staticfiles import StaticFiles

    test_engine = create_engine(db_url, future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    # Seed fixture data
    with TestSession() as session:
        seed_fixture_data(session)
        session.commit()

    # Patch the DB dependency used by web routes
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


def test_root_redirects_to_runs(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (301, 302, 307, 308)
    assert resp.headers["location"].endswith("/runs")


def test_recent_runs_page_loads(client):
    resp = client.get("/runs")
    assert resp.status_code == 200
    body = resp.text
    # The fixture run title should appear
    assert "Solo builders" in body or "self-hosted" in body or "Fixture Demo" in body


def test_recent_runs_page_shows_run_columns(client):
    resp = client.get("/runs")
    assert resp.status_code == 200
    body = resp.text
    # Should show phase, counts and a link to run detail
    assert "/runs/1" in body or 'href="/runs/' in body


def test_recent_runs_page_shows_fixture_badge(client):
    resp = client.get("/runs")
    assert resp.status_code == 200
    assert "fixture" in resp.text


def test_run_detail_page_loads(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200


def test_run_detail_shows_run_title(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    body = resp.text
    assert "Solo builders" in body or "self-hosted" in body or "Fixture Demo" in body


def test_run_detail_shows_sources_section(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    assert "Sources" in resp.text


def test_run_detail_shows_claims_section(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    assert "Claims" in resp.text


def test_run_detail_shows_themes_section(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    assert "Themes" in resp.text


def test_run_detail_shows_candidates_section(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    assert "Candidates" in resp.text


def test_run_detail_shows_validation_gates_section(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    assert "Validation Gates" in resp.text


def test_run_detail_shows_review_statuses(client):
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    body = resp.text
    # Fixture data has unreviewed, weak, or disputed claims/candidates
    assert any(s in body for s in ["unreviewed", "weak", "disputed", "accepted", "needs followup"])


def test_run_detail_404_for_missing_run(client):
    resp = client.get("/runs/99999")
    assert resp.status_code == 404


def test_health_still_works(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
