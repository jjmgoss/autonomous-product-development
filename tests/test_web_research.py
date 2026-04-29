from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from apd.app.db import Base
from apd.domain.models import EvidenceExcerpt, ResearchBrief, Run, Source
from apd.services.model_execution_settings import save_model_execution_settings
from apd.services.research_brief_service import create_brief
from apd.services import web_research


@pytest.fixture()
def db(tmp_path):
    db_path = tmp_path / "test_web_research.db"
    engine = create_engine(
        f"sqlite+pysqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with Session() as session:
        yield session


@pytest.fixture()
def client_and_session(tmp_path, monkeypatch):
    db_path = tmp_path / "test_web_research_client.db"
    db_url = f"sqlite+pysqlite:///{db_path}"
    test_engine = create_engine(
        db_url,
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    import apd.app.db as app_db
    import apd.web.routes as web_routes

    monkeypatch.setattr(app_db, "engine", test_engine)
    monkeypatch.setattr(app_db, "SessionLocal", TestSession)

    def _override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    from apd.app.main import app
    from fastapi.testclient import TestClient

    app.dependency_overrides[web_routes._get_db] = _override_get_db

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client, TestSession

    app.dependency_overrides.clear()


def _save_ui_model_settings(db):
    save_model_execution_settings(
        db,
        {
            "provider": "ollama",
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llama3",
            "ollama_timeout_seconds": 120,
            "ollama_keep_alive": 0,
            "component_repair_attempts": 2,
            "enabled": True,
        },
    )


def test_run_web_research_stores_source_and_excerpt(db, monkeypatch):
    _save_ui_model_settings(db)
    brief = create_brief(db, title="Maintenance pain", research_question="What public evidence exists?")

    monkeypatch.setattr(
        web_research,
        "_ollama_generate",
        lambda config, payload: (
            {
                "response": json.dumps(
                    {
                        "schema_version": "1.0",
                        "queries": [{"query": "self host maintenance pain", "rationale": "Find public complaints"}],
                        "urls": [{"url": "https://example.com/thread", "rationale": "Relevant public thread"}],
                    }
                )
            },
            None,
        ),
    )
    monkeypatch.setattr(
        web_research,
        "fetch_public_url",
        lambda url, **kwargs: {
            "success": True,
            "status_code": 200,
            "content_type": "text/html; charset=utf-8",
            "body": b"<html><title>Public thread</title><body>Solo operators keep losing a day each month to backup checks.</body></html>",
        },
    )

    result = web_research.run_web_research_for_brief(db, brief)

    assert result["status"] == "completed"
    assert result["fetched_source_count"] == 1

    saved_run = db.scalar(select(Run).where(Run.id == result["web_research_run_id"]))
    saved_source = db.scalar(select(Source).where(Source.run_id == saved_run.id))
    saved_excerpt = db.scalar(select(EvidenceExcerpt).where(EvidenceExcerpt.source_id == saved_source.id))
    saved_brief = db.get(ResearchBrief, brief.id)

    assert saved_run is not None
    assert saved_source is not None
    assert saved_source.source_type == "public_web"
    assert saved_source.url == "https://example.com/thread"
    assert saved_excerpt is not None
    assert "backup checks" in saved_excerpt.excerpt_text
    assert saved_brief.metadata_json["web_research_run_id"] == result["web_research_run_id"]


@pytest.mark.parametrize(
    ("url", "reason"),
    [
        ("file:///tmp/nope", "unsupported_scheme"),
        ("http://localhost:8080/test", "local_host_not_allowed"),
        ("http://127.0.0.1/test", "private_or_loopback_ip_not_allowed"),
    ],
)
def test_validate_public_url_rejects_private_or_non_http_targets(url, reason):
    normalized, error = web_research.validate_public_url(url)
    assert normalized is None
    assert error == reason



def test_run_web_research_caps_url_fetches(db, monkeypatch):
    _save_ui_model_settings(db)
    brief = create_brief(db, title="Cap URLs", research_question="How many URLs are fetched?")
    fetch_calls: list[str] = []

    urls = [{"url": f"https://example.com/{index}", "rationale": "candidate"} for index in range(7)]
    monkeypatch.setattr(
        web_research,
        "_ollama_generate",
        lambda config, payload: ({"response": json.dumps({"schema_version": "1.0", "queries": [], "urls": urls})}, None),
    )
    monkeypatch.setattr(
        web_research,
        "fetch_public_url",
        lambda url, **kwargs: fetch_calls.append(url) or {
            "success": True,
            "status_code": 200,
            "content_type": "text/plain",
            "body": b"public text",
        },
    )

    result = web_research.run_web_research_for_brief(db, brief)

    assert result["status"] == "completed"
    assert len(fetch_calls) == web_research.MAX_FETCH_URLS
    assert f"capped_urls_at_{web_research.MAX_FETCH_URLS}" in result["warnings"]



def test_run_web_research_rejects_invalid_urls_without_fetching(db, monkeypatch):
    _save_ui_model_settings(db)
    brief = create_brief(db, title="Reject bad URLs", research_question="Reject invalid URLs")

    monkeypatch.setattr(
        web_research,
        "_ollama_generate",
        lambda config, payload: (
            {
                "response": json.dumps(
                    {
                        "schema_version": "1.0",
                        "queries": [{"query": "backup toil forums", "rationale": "future search"}],
                        "urls": [
                            {"url": "file:///tmp/private", "rationale": "bad"},
                            {"url": "http://localhost:9999/admin", "rationale": "bad"},
                        ],
                    }
                )
            },
            None,
        ),
    )

    def _should_not_fetch(url, **kwargs):
        raise AssertionError(f"fetch_public_url should not be called for {url}")

    monkeypatch.setattr(web_research, "fetch_public_url", _should_not_fetch)

    result = web_research.run_web_research_for_brief(db, brief)

    assert result["status"] == "no_valid_urls"
    assert result["fetched_source_count"] == 0
    reasons = {item["reason"] for item in result["skipped_urls"]}
    assert "unsupported_scheme" in reasons
    assert "local_host_not_allowed" in reasons



def test_run_web_research_records_fetch_failures_without_crashing(db, monkeypatch):
    _save_ui_model_settings(db)
    brief = create_brief(db, title="Fetch failures", research_question="Handle failed fetches")

    monkeypatch.setattr(
        web_research,
        "_ollama_generate",
        lambda config, payload: (
            {
                "response": json.dumps(
                    {
                        "schema_version": "1.0",
                        "queries": [],
                        "urls": [{"url": "https://example.com/fail", "rationale": "probe"}],
                    }
                )
            },
            None,
        ),
    )
    monkeypatch.setattr(
        web_research,
        "fetch_public_url",
        lambda url, **kwargs: {"success": False, "error": "timeout"},
    )

    result = web_research.run_web_research_for_brief(db, brief)

    assert result["status"] == "no_valid_urls"
    assert result["fetched_source_count"] == 0
    assert result["skipped_urls"] == [{"url": "https://example.com/fail", "reason": "timeout"}]



def test_capture_only_web_discovery_route_renders_phase_status(client_and_session, monkeypatch):
    client, TestSession = client_and_session

    response = client.post(
        "/briefs",
        data={"title": "UI brief", "research_question": "What is the signal?"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    brief_id = int(response.headers["location"].split("/")[-1])

    def _fake_run_web_research_for_brief(db, brief):
        return {
            "status": "completed",
            "started_at": "2026-04-28T00:00:00+00:00",
            "finished_at": "2026-04-28T00:00:02+00:00",
            "success": True,
            "proposed_query_count": 1,
            "proposed_url_count": 1,
            "fetched_source_count": 1,
            "errors": [],
            "warnings": [],
            "queries": [{"query": "support escalation pain", "rationale": "seed"}],
            "sources": [{"url": "https://example.com/article", "title": "Example article"}],
            "skipped_urls": [],
        }

    import apd.web.routes as web_routes

    monkeypatch.setattr(web_routes, "run_web_research_for_brief", _fake_run_web_research_for_brief)

    response = client.post(f"/briefs/{brief_id}/research-web", follow_redirects=True)
    assert response.status_code == 200
    assert "Web discovery phase" in response.text
    assert "Example article" in response.text
    assert "support escalation pain" in response.text
    assert "issue #63" in response.text
