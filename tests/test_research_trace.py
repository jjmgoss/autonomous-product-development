from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest

from apd.app.db import Base
from apd.domain.models import Run, RunPhase
from apd.services.research_brief_service import create_brief
from apd.services.research_trace import (
    append_research_trace_event,
    attach_run_to_trace_events,
    create_trace_correlation_id,
    list_research_trace_events,
)


@pytest.fixture()
def db(tmp_path):
    db_path = tmp_path / "test_research_trace.db"
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
    db_path = tmp_path / "test_research_trace_client.db"
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


def test_trace_event_helpers_create_retrieve_and_attach_run(db):
    brief = create_brief(db, title="Trace brief", research_question="Q")
    run = Run(title="Trace run", intent="Q", phase=RunPhase.EVIDENCE_COLLECTED)
    db.add(run)
    db.flush()

    correlation_id = create_trace_correlation_id(brief_id=brief.id)
    append_research_trace_event(
        db,
        brief_id=brief.id,
        correlation_id=correlation_id,
        event_type="phase_started",
        phase="web_discovery",
        message="Trace started.",
        payload={
            "api_key": "super-secret",
            "raw_path": r"C:\Users\jjmgo\private.txt",
            "url": "https://example.com/thread?token=hidden",
        },
    )
    append_research_trace_event(
        db,
        brief_id=brief.id,
        correlation_id=correlation_id,
        event_type="validation_failed",
        phase="claim_theme_batch",
        payload={"errors": ["missing excerpt"]},
    )

    events = list_research_trace_events(db, brief_id=brief.id, correlation_id=correlation_id)

    assert len(events) == 2
    assert events[0].payload_json["api_key"] == "[redacted]"
    assert events[0].payload_json["raw_path"] == "[redacted]"
    assert events[0].payload_json["url"] == "https://example.com/thread"

    attached_count = attach_run_to_trace_events(db, correlation_id=correlation_id, run_id=run.id)
    run_events = list_research_trace_events(db, run_id=run.id)

    assert attached_count == 2
    assert len(run_events) == 2


def test_brief_detail_renders_trace_events_in_collapsed_section(client_and_session):
    client, TestSession = client_and_session

    with TestSession() as db:
        brief = create_brief(db, title="Trace UI brief", research_question="What happened?")
        brief_id = brief.id
        correlation_id = create_trace_correlation_id(brief_id=brief.id)
        append_research_trace_event(
            db,
            brief_id=brief.id,
            correlation_id=correlation_id,
            event_type="validation_failed",
            phase="claim_theme_batch",
            message="Grounding mismatch detected.",
            payload={"authorization": "Bearer secret-token", "error": "unknown grounded source_id"},
        )
        brief.metadata_json = {
            "last_execution": {
                "status": "component_validation_failed",
                "trace_correlation_id": correlation_id,
                "errors": ["component_execution: claim_theme_batch failed"],
            }
        }
        db.add(brief)
        db.commit()

    response = client.get(f"/briefs/{brief_id}")

    assert response.status_code == 200
    assert "Show trace events (1)" in response.text
    assert "Grounding mismatch detected." in response.text
    assert "validation_failed" in response.text
    assert "[redacted]" in response.text