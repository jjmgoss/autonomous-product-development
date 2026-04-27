"""Tests for research execution paths (stub + Ollama)."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest

from apd.app.db import Base
from apd.services.research_brief_service import create_brief, get_brief
from apd.services.research_execution_ollama import (
    execute_research_brief_ollama,
    extract_json_object_from_model_output,
    get_ollama_execution_config,
)
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


def test_ollama_config_detection_missing_env(monkeypatch):
    monkeypatch.delenv("APD_MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("APD_OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("APD_OLLAMA_MODEL", raising=False)

    config, missing = get_ollama_execution_config()
    assert config is None
    assert "APD_MODEL_PROVIDER=ollama" in missing
    assert "APD_OLLAMA_BASE_URL" in missing
    assert "APD_OLLAMA_MODEL" in missing


def test_extract_json_object_plain_json():
    text = '{"run":{"title":"T","intent":"I"},"claims":[{"id":"c1","statement":"S"}]}'
    parsed, parse_error = extract_json_object_from_model_output(text)
    assert parse_error is None
    assert parsed is not None
    assert parsed["run"]["title"] == "T"


def test_extract_json_object_from_fenced_block():
    text = """
    Here is your draft:
    ```json
    {"run":{"title":"T","intent":"I"},"claims":[{"id":"c1","statement":"S"}]}
    ```
    """
    parsed, parse_error = extract_json_object_from_model_output(text)
    assert parse_error is None
    assert parsed is not None
    assert parsed["run"]["intent"] == "I"


def test_execute_ollama_success_path_imports_run(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_OLLAMA_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="Ollama brief", research_question="Q")
    brief = get_brief(db, brief.id)

    def _fake_generate(config, payload):
        return (
            {
                "response": (
                    '{"schema_version":"1.0","external_draft_id":"ollama-1","agent_name":"ollama-test",'
                    '"run":{"title":"Ollama run","intent":"Q"},"claims":[{"id":"c1","statement":"S"}],'
                    '"candidates":[{"id":"cand-1","title":"Candidate 1","summary":"S"}]}'
                )
            },
            None,
        )

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)

    result = execute_research_brief_ollama(db, brief)
    assert result["success"] is True
    assert result["status"] == "imported"
    assert isinstance(result["run_id"], int)


def test_execute_ollama_unparseable_output_fails_without_import(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_OLLAMA_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="Bad parse", research_question="Q")
    brief = get_brief(db, brief.id)

    def _fake_generate(config, payload):
        return ({"response": "not json"}, None)

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)

    result = execute_research_brief_ollama(db, brief)
    assert result["success"] is False
    assert result["status"] == "parse_failed"
    assert result["run_id"] is None


def test_execute_ollama_validation_failure_repair_succeeds(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_OLLAMA_REPAIR_ATTEMPTS", "1")

    brief = create_brief(db, title="Repair brief", research_question="Q")
    brief = get_brief(db, brief.id)

    calls = {"count": 0}

    def _fake_generate(config, payload):
        calls["count"] += 1
        if calls["count"] == 1:
            # Missing required claims.statement (no alias field) to force repair.
            return (
                {
                    "response": (
                        '{"schema_version":"1.0","external_draft_id":"repair-1","agent_name":"ollama-test",'
                        '"run":{"title":"R","intent":"Q"},"claims":[{"id":"c1"}]}'
                    )
                },
                None,
            )
        return (
            {
                "response": (
                    '{"schema_version":"1.0","external_draft_id":"repair-1b","agent_name":"ollama-test",'
                    '"run":{"title":"R2","intent":"Q"},"claims":[{"id":"c1","statement":"fixed"}],'
                    '"candidates":[{"id":"cand-1","title":"Candidate 1"}]}'
                )
            },
            None,
        )

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)

    result = execute_research_brief_ollama(db, brief)
    assert calls["count"] == 2
    assert result["success"] is True
    assert result["status"] == "imported"
    assert isinstance(result["run_id"], int)


def test_execute_ollama_zero_candidate_fails_quality_gate(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_OLLAMA_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="No candidates", research_question="Q")
    brief = get_brief(db, brief.id)

    def _fake_generate(config, payload):
        return (
            {
                "response": (
                    '{"schema_version":"1.0","external_draft_id":"qc-1","agent_name":"ollama-test",'
                    '"run":{"title":"R","intent":"Q"},"claims":[{"id":"c1","statement":"S"}]}'
                )
            },
            None,
        )

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama(db, brief)
    assert result["success"] is False
    assert result["status"] == "quality_failed_no_candidates"
    assert result["run_id"] is None
    assert any("no product candidates" in err.lower() for err in result["errors"])


def test_execute_ollama_source_url_adds_quality_warning(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_OLLAMA_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="URL warning", research_question="Q")
    brief = get_brief(db, brief.id)

    def _fake_generate(config, payload):
        return (
            {
                "response": (
                    '{"schema_version":"1.0","external_draft_id":"qc-2","agent_name":"ollama-test",'
                    '"run":{"title":"R","intent":"Q"},"sources":[{"id":"src-1","source_type":"forum","url":"https://example.com"}],'
                    '"candidates":[{"id":"cand-1","title":"Candidate 1"}]}'
                )
            },
            None,
        )

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama(db, brief)
    assert result["success"] is True
    assert result["status"] == "imported"
    assert "quality_warning_unprovided_source_urls" in result["warnings"]


def test_execute_ollama_payload_defaults_keep_alive_zero_and_uses_strict_prompt(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.delenv("APD_OLLAMA_KEEP_ALIVE", raising=False)
    monkeypatch.setenv("APD_OLLAMA_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="Prompt+payload", research_question="Q")
    brief = get_brief(db, brief.id)
    captured_payloads = []

    def _fake_generate(config, payload):
        captured_payloads.append(payload)
        return (
            {
                "response": (
                    '{"schema_version":"1.0","external_draft_id":"qc-3","agent_name":"ollama-test",'
                    '"run":{"title":"R","intent":"Q"},"candidates":[{"id":"cand-1","title":"Candidate 1"}]}'
                )
            },
            None,
        )

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama(db, brief)
    assert result["success"] is True
    assert captured_payloads
    first_payload = captured_payloads[0]
    assert first_payload.get("keep_alive") == 0
    assert "product investigation system" in first_payload.get("prompt", "").lower()
    assert "do not invent sources" in first_payload.get("prompt", "").lower()


def test_start_research_ollama_route_uses_mocked_service(client, monkeypatch):
    resp = client.post("/briefs", data={"title": "Web ollama", "research_question": "What is X?"}, follow_redirects=False)
    assert resp.status_code == 303
    brief_id = int(resp.headers["location"].split("/")[-1])

    monkeypatch.setattr(
        "apd.web.routes.get_ollama_execution_config",
        lambda: (
            type("Cfg", (), {"model": "llama3"})(),
            [],
        ),
    )
    monkeypatch.setattr(
        "apd.web.routes.execute_research_brief_ollama",
        lambda db, brief: {
            "success": False,
            "provider": "ollama",
            "model": "llama3",
            "status": "validation_failed",
            "started_at": "2026-01-01T00:00:00+00:00",
            "finished_at": "2026-01-01T00:00:01+00:00",
            "errors": ["mocked failure"],
            "warnings": [],
            "run_id": None,
        },
    )

    resp2 = client.post(f"/briefs/{brief_id}/start-research-ollama", follow_redirects=True)
    assert resp2.status_code == 200
    assert "mocked failure" in resp2.text


def test_start_research_ollama_route_handles_missing_config(client, monkeypatch):
    resp = client.post("/briefs", data={"title": "Web ollama config", "research_question": "What is X?"}, follow_redirects=False)
    assert resp.status_code == 303
    brief_id = int(resp.headers["location"].split("/")[-1])

    monkeypatch.setattr(
        "apd.web.routes.get_ollama_execution_config",
        lambda: (None, ["APD_MODEL_PROVIDER=ollama", "APD_OLLAMA_MODEL"]),
    )

    resp2 = client.post(f"/briefs/{brief_id}/start-research-ollama", follow_redirects=True)
    assert resp2.status_code == 200
    assert "Missing required env" in resp2.text
    assert "APD_OLLAMA_MODEL" in resp2.text


def test_stub_route_still_works_when_ollama_path_exists(client):
    resp = client.post("/briefs", data={"title": "Stub still works", "research_question": "What is X?"}, follow_redirects=False)
    assert resp.status_code == 303
    brief_id = int(resp.headers["location"].split("/")[-1])

    resp2 = client.post(f"/briefs/{brief_id}/start-research", follow_redirects=True)
    assert resp2.status_code == 200
    assert "Stub still works" in resp2.text


