from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from apd.app.db import Base
from apd.domain.models import EvidenceExcerpt, ResearchBrief, Run, RunPhase, Source
from apd.services.model_execution_settings import save_model_execution_settings
from apd.services.research_brief_service import create_brief
from apd.services.research_search import StaticSearchProvider
from apd.services.research_trace import list_research_trace_events
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


def _static_provider(fixtures_by_query):
    return StaticSearchProvider(fixtures_by_query, provider_name="static-test")


def test_run_web_research_stores_source_and_excerpt(db, monkeypatch):
    _save_ui_model_settings(db)
    brief = create_brief(db, title="Maintenance pain", research_question="What public evidence exists?")
    queries = web_research.generate_search_queries_for_brief(brief)

    provider = _static_provider(
        {
            queries[0].query: [
                {
                    "title": "Public thread",
                    "url": "https://example.com/thread",
                    "snippet": "Solo operators keep losing a day each month to backup checks.",
                }
            ]
        }
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

    result = web_research.run_web_research_for_brief(
        db,
        brief,
        trace_correlation_id="trace-web-success",
        search_provider=provider,
    )

    assert result["status"] == "completed"
    assert result["fetched_source_count"] == 1
    assert result["triage_counts"] == {"keep": 1, "discard": 0, "bait": 0, "uncertain": 0}
    assert result["discovery_summary"]["candidate_result_count"] == 1
    assert result["candidate_decisions"][0]["decision"] == "keep"
    assert result["weak_discovery_warning"] is not None
    trace_events = list_research_trace_events(db, brief_id=brief.id, correlation_id=result["trace_correlation_id"])
    trace_event_types = [event.event_type for event in trace_events]

    saved_run = db.scalar(select(Run).where(Run.id == result["web_research_run_id"]))
    saved_source = db.scalar(select(Source).where(Source.run_id == saved_run.id))
    saved_excerpt = db.scalar(select(EvidenceExcerpt).where(EvidenceExcerpt.source_id == saved_source.id))
    saved_brief = db.get(ResearchBrief, brief.id)

    assert saved_run is not None
    assert saved_source is not None
    assert saved_source.source_type == "forum_thread"
    assert saved_source.url == "https://example.com/thread"
    assert saved_excerpt is not None
    assert "backup checks" in saved_excerpt.excerpt_text
    assert saved_brief.metadata_json["web_research_run_id"] == result["web_research_run_id"]
    assert "phase_started" in trace_event_types
    assert "skill_context_selected" in trace_event_types
    assert "search_queries_generated" in trace_event_types
    assert "search_provider_called" in trace_event_types
    assert "search_result_collected" in trace_event_types
    assert "search_result_triaged" in trace_event_types
    assert "search_result_kept" in trace_event_types
    assert "search_source_fetch_started" in trace_event_types
    assert "search_source_fetch_completed" in trace_event_types
    assert "tool_call_started" in trace_event_types
    assert "tool_call_completed" in trace_event_types
    assert "source_fetched" in trace_event_types
    assert "discovery_completed" in trace_event_types
    assert "phase_completed" in trace_event_types


def test_get_grounding_source_packet_for_brief_includes_captured_ids_and_text(db):
    brief = create_brief(db, title="Grounded packet", research_question="Q")

    capture_run = Run(
        title="Grounding capture",
        intent="Q",
        mode="web_research_capture",
        phase=RunPhase.EVIDENCE_COLLECTED,
        metadata_json={"brief_id": brief.id, "created_by": "apd_web_research"},
    )
    db.add(capture_run)
    db.flush()

    source = Source(
        run_id=capture_run.id,
        title="Example source",
        source_type="public_web",
        url="https://example.com/source",
        origin="example.com",
        metadata_json={"brief_id": brief.id},
    )
    db.add(source)
    db.flush()

    excerpt = EvidenceExcerpt(
        run_id=capture_run.id,
        source_id=source.id,
        excerpt_text="Operators describe losing hours every week to manual incident triage.",
        excerpt_type="web_capture",
        metadata_json={"brief_id": brief.id},
    )
    db.add(excerpt)
    db.flush()

    brief.metadata_json = {"web_research_run_id": capture_run.id}
    db.add(brief)
    db.commit()

    packet = web_research.get_grounding_source_packet_for_brief(db, brief)
    rendered = web_research.render_grounding_source_packet(packet)

    assert len(packet.sources) == 1
    assert len(packet.evidence_excerpts) == 1
    assert packet.sources[0]["id"] == f"captured-source-{source.id}"
    assert packet.evidence_excerpts[0]["id"] == f"captured-excerpt-{excerpt.id}"
    assert packet.evidence_excerpts[0]["source_id"] == f"captured-source-{source.id}"
    assert "Example source" in rendered
    assert "manual incident triage" in rendered


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
    queries = web_research.generate_search_queries_for_brief(brief)

    provider = _static_provider(
        {
            queries[0].query: [
                {
                    "title": f"Forum thread {index}",
                    "url": f"https://example.com/thread-{index}",
                    "snippet": "Operators describe recurring pain and manual work.",
                }
                for index in range(4)
            ],
            queries[1].query: [
                {
                    "title": f"Forum thread extra {index}",
                    "url": f"https://example.com/thread-extra-{index}",
                    "snippet": "Operators describe recurring pain and manual work.",
                }
                for index in range(3)
            ],
        }
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

    result = web_research.run_web_research_for_brief(db, brief, search_provider=provider)

    assert result["status"] == "completed"
    assert len(fetch_calls) == web_research.MAX_FETCH_URLS
    assert f"capped_urls_at_{web_research.MAX_FETCH_URLS}" in result["warnings"]



def test_run_web_research_rejects_invalid_urls_without_fetching(db, monkeypatch):
    _save_ui_model_settings(db)
    brief = create_brief(db, title="Reject bad URLs", research_question="Reject invalid URLs")
    queries = web_research.generate_search_queries_for_brief(brief)

    provider = _static_provider(
        {
            queries[0].query: [
                {"title": "Forum thread", "url": "file:///tmp/thread/private", "snippet": "Invalid URL pain thread."},
                {"title": "Forum thread", "url": "http://localhost:9999/thread/admin", "snippet": "Invalid local URL pain thread."},
            ]
        }
    )

    def _should_not_fetch(url, **kwargs):
        raise AssertionError(f"fetch_public_url should not be called for {url}")

    monkeypatch.setattr(web_research, "fetch_public_url", _should_not_fetch)

    result = web_research.run_web_research_for_brief(
        db,
        brief,
        trace_correlation_id="trace-web-rejected",
        search_provider=provider,
    )
    trace_events = list_research_trace_events(db, brief_id=brief.id, correlation_id=result["trace_correlation_id"])
    rejected_payloads = [event.payload_json for event in trace_events if event.event_type == "url_rejected"]

    assert result["status"] == "no_valid_urls"
    assert result["fetched_source_count"] == 0
    assert result["candidate_decisions"][0]["rejection_error"] == "unsupported_scheme"
    reasons = {item["reason"] for item in result["skipped_urls"]}
    assert "unsupported_scheme" in reasons
    assert "local_host_not_allowed" in reasons
    assert len(rejected_payloads) == 2
    assert {payload["reason"] for payload in rejected_payloads} == {"unsupported_scheme", "local_host_not_allowed"}



def test_run_web_research_records_fetch_failures_without_crashing(db, monkeypatch):
    _save_ui_model_settings(db)
    brief = create_brief(db, title="Fetch failures", research_question="Handle failed fetches")
    queries = web_research.generate_search_queries_for_brief(brief)

    provider = _static_provider(
        {
            queries[0].query: [
                {"title": "Forum thread", "url": "https://example.com/thread/fail", "snippet": "Handle failed fetch pain thread."}
            ]
        }
    )
    monkeypatch.setattr(
        web_research,
        "fetch_public_url",
        lambda url, **kwargs: {"success": False, "error": "timeout"},
    )

    result = web_research.run_web_research_for_brief(db, brief, search_provider=provider)

    assert result["status"] == "no_valid_urls"
    assert result["fetched_source_count"] == 0
    assert result["candidate_decisions"][0]["rejection_error"] == "timeout"
    assert result["skipped_urls"] == [{"url": "https://example.com/thread/fail", "reason": "timeout"}]



def test_capture_only_web_discovery_route_renders_phase_status(client_and_session, monkeypatch):
    client, TestSession = client_and_session

    response = client.post(
        "/briefs",
        data={"title": "UI brief", "research_question": "What is the signal?"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    brief_id = int(response.headers["location"].split("/")[-1])

    def _fake_run_web_research_for_brief(db, brief, trace_correlation_id=None):
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
            "trace_correlation_id": trace_correlation_id,
        }

    import apd.web.routes as web_routes

    monkeypatch.setattr(web_routes, "run_web_research_for_brief", _fake_run_web_research_for_brief)

    response = client.post(f"/briefs/{brief_id}/research-web", follow_redirects=True)
    assert response.status_code == 200
    assert "Web discovery phase" in response.text
    assert "Example article" in response.text
    assert "support escalation pain" in response.text
    assert "grounded component execution" in response.text
    assert "does not verify truth" in response.text
