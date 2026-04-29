"""Tests for research execution paths (stub + Ollama)."""

from __future__ import annotations

from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest

from apd.app.db import Base
from apd.domain.models import EvidenceExcerpt, Run, RunPhase, Source
from apd.services.research_components import (
    ComponentDraftAssembler,
    parse_component_batch_from_data,
)
from apd.services.research_brief_service import create_brief, get_brief
from apd.services.research_execution_ollama import (
    execute_research_brief_ollama_components,
    execute_research_brief_ollama_components_grounded,
    execute_research_brief_ollama,
    extract_json_object_from_model_output,
    get_ollama_execution_config,
)
from apd.services.research_execution_stub import execute_research_brief_stub


def _clear_ollama_env(monkeypatch):
    monkeypatch.delenv("APD_MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("APD_OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("APD_OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("APD_OLLAMA_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("APD_OLLAMA_KEEP_ALIVE", raising=False)
    monkeypatch.delenv("APD_OLLAMA_REPAIR_ATTEMPTS", raising=False)
    monkeypatch.delenv("APD_COMPONENT_REPAIR_ATTEMPTS", raising=False)


def _save_ui_model_settings(client):
    response = client.post(
        "/settings/model-execution",
        data={
            "provider": "ollama",
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llama3",
            "ollama_timeout_seconds": "120",
            "ollama_keep_alive": "0",
            "component_repair_attempts": "2",
            "enabled": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def _create_brief_via_ui(client, *, title: str) -> int:
    response = client.post(
        "/briefs",
        data={"title": title, "research_question": "What is X?"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    location = response.headers["location"]
    return int(location.split("/")[-1])


def _seed_captured_web_source(db, brief, *, title: str = "Captured source"):
    capture_run = Run(
        title=f"{brief.title} capture",
        intent=brief.research_question,
        mode="web_research_capture",
        phase=RunPhase.EVIDENCE_COLLECTED,
        metadata_json={"brief_id": brief.id, "created_by": "apd_web_research"},
    )
    db.add(capture_run)
    db.flush()

    source = Source(
        run_id=capture_run.id,
        title=title,
        source_type="public_web",
        url="https://example.com/captured",
        origin="example.com",
        metadata_json={"brief_id": brief.id},
    )
    db.add(source)
    db.flush()

    excerpt = EvidenceExcerpt(
        run_id=capture_run.id,
        source_id=source.id,
        excerpt_text="Teams keep losing time because handoff context is missing.",
        excerpt_type="web_capture",
        metadata_json={"brief_id": brief.id},
    )
    db.add(excerpt)
    db.flush()

    brief.metadata_json = {"web_research_run_id": capture_run.id}
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return source, excerpt


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


def test_start_research_route_uses_current_best_path(client, monkeypatch):
    resp = client.post("/briefs", data={"title": "Web path", "research_question": "What is X?"}, follow_redirects=False)
    assert resp.status_code == 303
    brief_id = int(resp.headers["location"].split("/")[-1])

    monkeypatch.setattr(
        "apd.web.routes.start_research_ollama_components",
        lambda brief_id, db: RedirectResponse(url="/runs/123", status_code=303),
    )

    resp2 = client.post(f"/briefs/{brief_id}/start-research", follow_redirects=False)
    assert resp2.status_code == 303
    assert resp2.headers["location"] == "/runs/123"


def test_start_research_stub_route_creates_run(client):
    resp = client.post("/briefs", data={"title": "Web stub", "research_question": "What is X?"}, follow_redirects=False)
    assert resp.status_code == 303
    location = resp.headers["location"]
    assert location.startswith("/briefs/")
    brief_id = int(location.split("/")[-1])

    resp2 = client.post(f"/briefs/{brief_id}/start-research-stub", follow_redirects=True)
    assert resp2.status_code == 200
    assert "Web stub" in resp2.text


def test_settings_page_save_and_reload_persists_saved_values(client, monkeypatch):
    _clear_ollama_env(monkeypatch)

    _save_ui_model_settings(client)

    response = client.get("/settings/model-execution")
    assert response.status_code == 200
    assert 'value="http://localhost:11434"' in response.text
    assert 'value="llama3"' in response.text


def test_brief_detail_shows_single_start_research_action_from_saved_db_settings(client, monkeypatch):
    _clear_ollama_env(monkeypatch)
    _save_ui_model_settings(client)
    brief_id = _create_brief_via_ui(client, title="DB-backed config brief")

    response = client.get(f"/briefs/{brief_id}")
    assert response.status_code == 200
    assert response.text.count("Start Research") == 1
    assert "Uses your configured local model to run APD's current autonomous research path." in response.text
    assert "Start Research with Ollama" not in response.text
    assert "Start web-assisted research (prototype)" not in response.text
    assert "Missing required env" not in response.text


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


def test_component_batch_valid_events_assemble_to_draft_package():
    raw_batch = {
        "schema_version": "1.0",
        "batch_id": "batch-1",
        "events": [
            {
                "schema_version": "1.0",
                "event_type": "candidate.proposed",
                "external_id": "cand-1",
                "payload": {"title": "Candidate A", "summary": "S"},
            },
            {
                "schema_version": "1.0",
                "event_type": "claim.proposed",
                "external_id": "claim-1",
                "payload": {"statement": "Claim text"},
            },
            {
                "schema_version": "1.0",
                "event_type": "theme.proposed",
                "external_id": "theme-1",
                "payload": {"name": "Theme A"},
            },
        ],
    }
    batch, errors = parse_component_batch_from_data(raw_batch)
    assert batch is not None
    assert not errors

    assembler = ComponentDraftAssembler(
        run_title="Component run",
        run_intent="Q",
        agent_name="component-test",
        external_draft_id="ext-1",
    )
    result = assembler.apply_batch(batch)
    assert result.success is True
    assert result.package is not None
    assert len(result.package["candidates"]) == 1
    assert len(result.package["claims"]) == 1
    assert len(result.package["themes"]) == 1


def test_component_batch_malformed_event_fails_validation():
    raw_batch = {
        "schema_version": "1.0",
        "events": [
            {
                "schema_version": "1.0",
                "event_type": "claim.proposed",
                # missing external_id
                "payload": {"statement": "Claim text"},
            }
        ],
    }
    batch, errors = parse_component_batch_from_data(raw_batch)
    assert batch is None
    assert errors


def test_execute_ollama_success_path_imports_run(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_OLLAMA_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="Ollama brief", research_question="Q")
    brief = get_brief(db, brief.id)

    captured_payloads = []

    def _fake_generate(config, payload):
        captured_payloads.append(payload)
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
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
    assert captured_payloads[0].get("keep_alive") == "5m"
    assert captured_payloads[-1].get("keep_alive") == 0


def test_start_research_ollama_uses_saved_db_settings(client, monkeypatch):
    _clear_ollama_env(monkeypatch)
    _save_ui_model_settings(client)
    brief_id = _create_brief_via_ui(client, title="Saved DB config ollama")

    captured_payloads = []

    def _fake_generate(config, payload):
        captured_payloads.append(payload)
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        return (
            {
                "response": (
                    '{"schema_version":"1.0","external_draft_id":"ollama-1","agent_name":"ollama-test",'
                    '"run":{"title":"Saved DB config ollama","intent":"What is X?"},'
                    '"claims":[{"id":"c1","statement":"S"}],'
                    '"candidates":[{"id":"cand-1","title":"Candidate 1","summary":"S"}]}'
                )
            },
            None,
        )

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)

    response = client.post(f"/briefs/{brief_id}/start-research-ollama", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/runs/")
    assert captured_payloads


def test_start_research_ollama_components_uses_saved_db_settings(client, monkeypatch):
    _clear_ollama_env(monkeypatch)
    _save_ui_model_settings(client)
    brief_id = _create_brief_via_ui(client, title="Saved DB config components")

    grounded_ids: dict[str, str] = {}

    def _fake_run_web_research_for_brief(db, brief):
        source, excerpt = _seed_captured_web_source(db, brief)
        grounded_ids["source_id"] = f"captured-source-{source.id}"
        grounded_ids["excerpt_id"] = f"captured-excerpt-{excerpt.id}"
        return {
            "success": True,
            "status": "completed",
            "started_at": "2026-04-28T00:00:00+00:00",
            "finished_at": "2026-04-28T00:00:01+00:00",
            "errors": [],
            "warnings": [],
            "proposed_query_count": 1,
            "proposed_url_count": 1,
            "fetched_source_count": 1,
            "queries": [{"query": "support escalation pain", "rationale": "seed"}],
            "sources": [{"url": "https://example.com/article", "title": "Example article"}],
            "skipped_urls": [],
            "web_research_run_id": 11,
        }

    monkeypatch.setattr("apd.web.routes.run_web_research_for_brief", _fake_run_web_research_for_brief)

    captured_payloads = []
    responses = [
        (
            {
                "response": (
                    '{"schema_version":"1.0","batch_id":"b-candidate","events":['
                    '{"schema_version":"1.0","event_type":"candidate.proposed","external_id":"cand-1","payload":{"title":"Candidate A","summary":"S"}}'
                    ']}'
                )
            },
            None,
        ),
        (
            {
                "response": (
                    '{"schema_version":"1.0","batch_id":"b-claim-theme","events":['
                        '{"schema_version":"1.0","event_type":"claim.proposed","external_id":"claim-1","payload":{"statement":"Claim A"}},'
                        '{"schema_version":"1.0","event_type":"theme.proposed","external_id":"theme-1","payload":{"name":"Theme A"}},'
                    '{"schema_version":"1.0","event_type":"evidence_link.added","external_id":"link-1","payload":{"source_id":"__SOURCE_ID__","excerpt_id":"__EXCERPT_ID__","target_type":"claim","target_id":"claim-1","relationship":"supports"}}'
                    ']}'
                )
            },
            None,
        ),
        (
            {
                "response": (
                    '{"schema_version":"1.0","batch_id":"b-gates","events":['
                    '{"schema_version":"1.0","event_type":"validation_gate.proposed","external_id":"gate-1","payload":{"name":"Gate A","phase":"supported_opportunity","candidate_id":"cand-1"}}'
                    ']}'
                )
            },
            None,
        ),
    ]

    def _fake_generate(config, payload):
        captured_payloads.append(payload)
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        response, error = responses.pop(0)
        if response.get("response") and grounded_ids:
            response = {
                **response,
                "response": response["response"].replace("__SOURCE_ID__", grounded_ids["source_id"]).replace(
                    "__EXCERPT_ID__", grounded_ids["excerpt_id"]
                ),
            }
        return response, error

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)

    response = client.post(f"/briefs/{brief_id}/start-research-ollama-components", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/runs/")
    assert captured_payloads
    assert "Use only the provided APD-captured source packet" in captured_payloads[0]["prompt"]


def test_brief_detail_shows_grounding_context_without_extra_action_buttons(client, monkeypatch):
    _clear_ollama_env(monkeypatch)
    _save_ui_model_settings(client)
    brief_id = _create_brief_via_ui(client, title="Grounded action brief")

    import apd.app.db as app_db
    from apd.services.research_brief_service import get_brief as _get_brief

    with app_db.SessionLocal() as db:
        brief = _get_brief(db, brief_id)
        _seed_captured_web_source(db, brief)

    response = client.get(f"/briefs/{brief_id}")
    assert response.status_code == 200
    assert "Captured grounding context available: 1 sources, 1 excerpts." in response.text
    assert "Start grounded component research" not in response.text


def test_web_assisted_research_records_web_discovery_phase_in_last_execution(client, monkeypatch):
    _clear_ollama_env(monkeypatch)
    _save_ui_model_settings(client)
    brief_id = _create_brief_via_ui(client, title="Web-assisted prototype")

    monkeypatch.setattr(
        "apd.web.routes.run_web_research_for_brief",
        lambda db, brief: {
            "success": True,
            "status": "completed",
            "started_at": "2026-04-28T00:00:00+00:00",
            "finished_at": "2026-04-28T00:00:02+00:00",
            "errors": [],
            "warnings": [],
            "proposed_query_count": 1,
            "proposed_url_count": 1,
            "fetched_source_count": 1,
            "queries": [{"query": "solo operator maintenance pain", "rationale": "seed"}],
            "sources": [{"url": "https://example.com/source", "title": "Captured source"}],
            "skipped_urls": [],
            "web_research_run_id": 12,
        },
    )
    monkeypatch.setattr(
        "apd.web.routes.execute_research_brief_ollama_components_grounded",
        lambda db, brief: {
            "success": False,
            "provider": "ollama-components-grounded",
            "status": "component_validation_failed",
            "started_at": "2026-04-28T00:00:03+00:00",
            "finished_at": "2026-04-28T00:00:04+00:00",
            "errors": ["component phase failed"],
            "warnings": [],
            "run_id": None,
            "mode": "grounded_component_execution",
            "last_phase": "claim_theme_batch",
            "attempts_by_phase": {"candidate_batch": 1, "claim_theme_batch": 2},
            "grounding_status": "failed",
            "grounding_errors": ["claim_theme_batch: unknown grounded source_id 'captured-source-9999'"],
            "grounding_source_count": 1,
            "grounding_excerpt_count": 1,
        },
    )

    response = client.post(f"/briefs/{brief_id}/start-research-ollama-components", follow_redirects=True)

    assert response.status_code == 200
    assert "Web discovery phase" in response.text
    assert "Captured source" in response.text
    assert "solo operator maintenance pain" in response.text
    assert "Web discovery succeeded; component generation failed validation." in response.text
    assert "Error summary" in response.text
    assert "Grounding status" in response.text
    assert "unknown grounded source_id" in response.text
    assert "Show raw execution details" in response.text


def test_execute_grounded_components_requires_captured_sources(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")

    brief = create_brief(db, title="No grounded sources", research_question="Q")
    brief = get_brief(db, brief.id)

    result = execute_research_brief_ollama_components_grounded(db, brief)

    assert result["success"] is False
    assert result["status"] == "grounding_missing_sources"
    assert result["grounding_status"] == "missing_sources"
    assert any("Run web discovery first" in err for err in result["grounding_errors"])


def test_execute_grounded_components_imports_run_with_grounded_evidence_links(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_COMPONENT_REPAIR_ATTEMPTS", "1")

    brief = create_brief(db, title="Grounded success", research_question="Q")
    brief = get_brief(db, brief.id)
    source, excerpt = _seed_captured_web_source(db, brief)
    grounded_source_id = f"captured-source-{source.id}"
    grounded_excerpt_id = f"captured-excerpt-{excerpt.id}"
    captured_payloads: list[dict] = []
    responses = [
        ({"response": '{"schema_version":"1.0","batch_id":"b-candidate","events":[{"schema_version":"1.0","event_type":"candidate.proposed","external_id":"cand-1","payload":{"title":"Grounded candidate","summary":"S"}}]}'}, None),
        ({"response": (
            '{"schema_version":"1.0","batch_id":"b-claim-theme","events":['
            '{"schema_version":"1.0","event_type":"claim.proposed","external_id":"claim-1","payload":{"statement":"Teams lose time during handoffs."}},'
            '{"schema_version":"1.0","event_type":"theme.proposed","external_id":"theme-1","payload":{"name":"Handoff context loss"}},'
            '{"schema_version":"1.0","event_type":"evidence_link.added","external_id":"link-1","payload":{"source_id":"' + grounded_source_id + '","excerpt_id":"' + grounded_excerpt_id + '","target_type":"claim","target_id":"claim-1","relationship":"supports","strength":"strong"}}'
            ']}'
        )}, None),
        ({"response": '{"schema_version":"1.0","batch_id":"b-gates","events":[{"schema_version":"1.0","event_type":"validation_gate.proposed","external_id":"gate-1","payload":{"name":"Confirm repeated buyer urgency","phase":"supported_opportunity","candidate_id":"cand-1"}}]}'}, None),
    ]

    def _fake_generate(config, payload):
        captured_payloads.append(payload)
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        return responses.pop(0)

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)

    result = execute_research_brief_ollama_components_grounded(db, brief)

    assert result["success"] is True
    assert result["status"] == "imported"
    assert result["grounding_status"] == "passed"
    assert isinstance(result["run_id"], int)
    assert grounded_source_id in captured_payloads[0]["prompt"]
    assert "Use only the provided APD-captured source packet" in captured_payloads[0]["prompt"]


def test_execute_grounded_components_rejects_unknown_source_id(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_COMPONENT_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="Grounded bad source", research_question="Q")
    brief = get_brief(db, brief.id)
    _, excerpt = _seed_captured_web_source(db, brief)
    grounded_excerpt_id = f"captured-excerpt-{excerpt.id}"

    responses = [
        ({"response": '{"schema_version":"1.0","batch_id":"b-candidate","events":[{"schema_version":"1.0","event_type":"candidate.proposed","external_id":"cand-1","payload":{"title":"Candidate","summary":"S"}}]}'}, None),
        ({"response": (
            '{"schema_version":"1.0","batch_id":"b-claim-theme","events":['
            '{"schema_version":"1.0","event_type":"claim.proposed","external_id":"claim-1","payload":{"statement":"Claim text"}},'
            '{"schema_version":"1.0","event_type":"evidence_link.added","external_id":"link-1","payload":{"source_id":"captured-source-9999","excerpt_id":"' + grounded_excerpt_id + '","target_type":"claim","target_id":"claim-1","relationship":"supports"}}'
            ']}'
        )}, None),
    ]

    def _fake_generate(config, payload):
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        return responses.pop(0)

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama_components_grounded(db, brief)
    assert result["success"] is False
    assert result["grounding_status"] == "failed"
    assert any("unknown grounded source_id" in err for err in result["grounding_errors"])


def test_execute_grounded_components_rejects_unknown_excerpt_id(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_COMPONENT_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="Grounded bad excerpt", research_question="Q")
    brief = get_brief(db, brief.id)
    source, _ = _seed_captured_web_source(db, brief)
    grounded_source_id = f"captured-source-{source.id}"

    responses = [
        ({"response": '{"schema_version":"1.0","batch_id":"b-candidate","events":[{"schema_version":"1.0","event_type":"candidate.proposed","external_id":"cand-1","payload":{"title":"Candidate","summary":"S"}}]}'}, None),
        ({"response": (
            '{"schema_version":"1.0","batch_id":"b-claim-theme","events":['
            '{"schema_version":"1.0","event_type":"claim.proposed","external_id":"claim-1","payload":{"statement":"Claim text"}},'
            '{"schema_version":"1.0","event_type":"evidence_link.added","external_id":"link-1","payload":{"source_id":"' + grounded_source_id + '","excerpt_id":"captured-excerpt-9999","target_type":"claim","target_id":"claim-1","relationship":"supports"}}'
            ']}'
        )}, None),
    ]

    def _fake_generate(config, payload):
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        return responses.pop(0)

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama_components_grounded(db, brief)
    assert result["success"] is False
    assert result["grounding_status"] == "failed"
    assert any("unknown grounded excerpt_id" in err for err in result["grounding_errors"])


def test_execute_grounded_components_requires_supporting_claim_evidence(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_COMPONENT_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="Grounded unsupported claim", research_question="Q")
    brief = get_brief(db, brief.id)
    _seed_captured_web_source(db, brief)

    responses = [
        ({"response": '{"schema_version":"1.0","batch_id":"b-candidate","events":[{"schema_version":"1.0","event_type":"candidate.proposed","external_id":"cand-1","payload":{"title":"Candidate","summary":"S"}}]}'}, None),
        ({"response": '{"schema_version":"1.0","batch_id":"b-claim-theme","events":[{"schema_version":"1.0","event_type":"claim.proposed","external_id":"claim-1","payload":{"statement":"Claim text"}}]}'}, None),
    ]

    def _fake_generate(config, payload):
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        return responses.pop(0)

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama_components_grounded(db, brief)
    assert result["success"] is False
    assert result["grounding_status"] == "failed"
    assert any("at least one claim needs a supporting grounded evidence link" in err for err in result["grounding_errors"])


def test_execute_ollama_components_success_path_imports_run(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_COMPONENT_REPAIR_ATTEMPTS", "2")

    brief = create_brief(db, title="Components brief", research_question="Q")
    brief = get_brief(db, brief.id)
    captured_payloads = []
    responses = [
        (
            {
                "response": (
                    '{"schema_version":"1.0","batch_id":"b-candidate","events":['
                    '{"schema_version":"1.0","event_type":"candidate.proposed","external_id":"cand-1","payload":{"title":"Candidate A","summary":"S"}}'
                    ']}'
                )
            },
            None,
        ),
        (
            {
                "response": (
                    '{"schema_version":"1.0","batch_id":"b-claim-theme","events":['
                    '{"schema_version":"1.0","event_type":"claim.proposed","external_id":"claim-1","payload":{"statement":"Claim A"}},'
                    '{"schema_version":"1.0","event_type":"theme.proposed","external_id":"theme-1","payload":{"name":"Theme A"}}'
                    ']}'
                )
            },
            None,
        ),
        (
            {
                "response": (
                    '{"schema_version":"1.0","batch_id":"b-gates","events":['
                    '{"schema_version":"1.0","event_type":"validation_gate.proposed","external_id":"gate-1","payload":{"name":"Gate A","phase":"supported_opportunity","candidate_id":"cand-1"}}'
                    ']}'
                )
            },
            None,
        ),
    ]

    def _fake_generate(config, payload):
        captured_payloads.append(payload)
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        return responses.pop(0)

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama_components(db, brief)
    assert result["success"] is True
    assert result["status"] == "imported"
    assert result["mode"] == "component_execution"
    assert result["attempts_by_phase"]["candidate_batch"] == 1
    assert result["attempts_by_phase"]["claim_theme_batch"] == 1
    assert result["attempts_by_phase"]["validation_gate_batch"] == 1
    assert isinstance(result["run_id"], int)
    assert captured_payloads
    assert captured_payloads[0].get("keep_alive") == "5m"
    assert captured_payloads[-1].get("keep_alive") == 0
    assert len(captured_payloads) == 4


def test_execute_ollama_components_zero_candidate_fails_before_import(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_COMPONENT_REPAIR_ATTEMPTS", "2")

    brief = create_brief(db, title="Components no candidate", research_question="Q")
    brief = get_brief(db, brief.id)
    call_count = {"count": 0}

    def _fake_generate(config, payload):
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        call_count["count"] += 1
        return (
            {
                "response": (
                    '{"schema_version":"1.0","batch_id":"b1","events":['
                    '{"schema_version":"1.0","event_type":"claim.proposed","external_id":"claim-1","payload":{"statement":"Claim A"}}'
                    ']}'
                )
            },
            None,
        )

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama_components(db, brief)
    assert result["success"] is False
    assert result["status"] == "quality_failed_no_candidates"
    assert result["last_phase"] == "candidate_batch"
    assert result["attempts_by_phase"]["candidate_batch"] == 3
    assert call_count["count"] == 3
    assert result["run_id"] is None


def test_execute_ollama_components_malformed_batch_does_not_import(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_COMPONENT_REPAIR_ATTEMPTS", "1")

    brief = create_brief(db, title="Components malformed", research_question="Q")
    brief = get_brief(db, brief.id)
    call_count = {"count": 0}

    def _fake_generate(config, payload):
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        call_count["count"] += 1
        return (
            {
                "response": (
                    '{"schema_version":"1.0","batch_id":"b1","events":['
                    '{"schema_version":"1.0","event_type":"candidate.proposed","payload":{"title":"Candidate A"}}'
                    ']}'
                )
            },
            None,
        )

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama_components(db, brief)
    assert result["success"] is False
    assert result["status"] == "quality_failed_no_candidates"
    assert result["attempts_by_phase"]["candidate_batch"] == 2
    assert call_count["count"] == 2
    assert result["run_id"] is None


def test_execute_ollama_components_candidate_repair_then_imports(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_COMPONENT_REPAIR_ATTEMPTS", "2")

    brief = create_brief(db, title="Components candidate repair", research_question="Q")
    brief = get_brief(db, brief.id)
    prompts: list[str] = []
    responses = [
        ({"response": '{"schema_version":"1.0","batch_id":"bad","events":[{"schema_version":"1.0","event_type":"candidate.proposed","payload":{"title":"Missing ID"}}]}'}, None),
        ({"response": '{"schema_version":"1.0","batch_id":"fixed","events":[{"schema_version":"1.0","event_type":"candidate.proposed","external_id":"cand-1","payload":{"title":"Candidate 1"}}]}'}, None),
        ({"response": '{"schema_version":"1.0","batch_id":"claims","events":[{"schema_version":"1.0","event_type":"claim.proposed","external_id":"claim-1","payload":{"statement":"Claim text"}}]}'}, None),
        ({"response": '{"schema_version":"1.0","batch_id":"gates","events":[{"schema_version":"1.0","event_type":"validation_gate.proposed","external_id":"gate-1","payload":{"name":"Gate A","phase":"supported_opportunity","candidate_id":"cand-1"}}]}'}, None),
    ]

    def _fake_generate(config, payload):
        prompts.append(payload.get("prompt", ""))
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        return responses.pop(0)

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama_components(db, brief)
    assert result["success"] is True
    assert result["status"] == "imported"
    assert result["attempts_by_phase"]["candidate_batch"] == 2
    assert "phase repair request" in prompts[1].lower()


def test_execute_ollama_components_candidate_repair_exhausted_fails(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_COMPONENT_REPAIR_ATTEMPTS", "2")

    brief = create_brief(db, title="Components candidate repair exhausted", research_question="Q")
    brief = get_brief(db, brief.id)
    call_count = {"count": 0}

    def _fake_generate(config, payload):
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        call_count["count"] += 1
        return (
            {
                "response": (
                    '{"schema_version":"1.0","batch_id":"still-bad","events":['
                    '{"schema_version":"1.0","event_type":"candidate.proposed","payload":{"title":"Missing ID"}}'
                    ']}'
                )
            },
            None,
        )

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama_components(db, brief)
    assert result["success"] is False
    assert result["status"] == "quality_failed_no_candidates"
    assert result["last_phase"] == "candidate_batch"
    assert result["attempts_by_phase"]["candidate_batch"] == 3
    assert call_count["count"] == 3


def test_execute_ollama_unparseable_output_fails_without_import(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_OLLAMA_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="Bad parse", research_question="Q")
    brief = get_brief(db, brief.id)

    def _fake_generate(config, payload):
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
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
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
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
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
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
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
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


def test_execute_ollama_payload_keeps_model_warm_then_unloads_and_uses_strict_prompt(db, monkeypatch):
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
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
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
    assert first_payload.get("keep_alive") == "5m"
    assert "product investigation system" in first_payload.get("prompt", "").lower()
    assert "do not invent sources" in first_payload.get("prompt", "").lower()
    assert captured_payloads[-1].get("keep_alive") == 0
    assert not str(captured_payloads[-1].get("prompt", "")).strip()


def test_execute_ollama_explicit_keep_alive_respected_without_forced_unload(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_OLLAMA_KEEP_ALIVE", "10m")
    monkeypatch.setenv("APD_OLLAMA_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="Keep-alive explicit", research_question="Q")
    brief = get_brief(db, brief.id)
    captured_payloads = []

    def _fake_generate(config, payload):
        captured_payloads.append(payload)
        return (
            {
                "response": (
                    '{"schema_version":"1.0","external_draft_id":"qc-4","agent_name":"ollama-test",'
                    '"run":{"title":"R","intent":"Q"},"candidates":[{"id":"cand-1","title":"Candidate 1"}]}'
                )
            },
            None,
        )

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama(db, brief)
    assert result["success"] is True
    assert len(captured_payloads) == 1
    assert captured_payloads[0].get("keep_alive") == "10m"


def test_execute_ollama_components_attempts_unload_after_run(db, monkeypatch):
    monkeypatch.setenv("APD_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("APD_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("APD_OLLAMA_MODEL", "llama3")
    monkeypatch.setenv("APD_COMPONENT_REPAIR_ATTEMPTS", "0")

    brief = create_brief(db, title="Components unload", research_question="Q")
    brief = get_brief(db, brief.id)
    captured_payloads = []
    responses = [
        ({"response": '{"schema_version":"1.0","batch_id":"b1","events":[{"schema_version":"1.0","event_type":"candidate.proposed","external_id":"cand-1","payload":{"title":"Candidate 1"}}]}'}, None),
        ({"response": '{"schema_version":"1.0","batch_id":"b2","events":[{"schema_version":"1.0","event_type":"claim.proposed","external_id":"claim-1","payload":{"statement":"Claim 1"}}]}'}, None),
        ({"response": '{"schema_version":"1.0","batch_id":"b3","events":[{"schema_version":"1.0","event_type":"validation_gate.proposed","external_id":"gate-1","payload":{"name":"Gate 1","phase":"supported_opportunity","candidate_id":"cand-1"}}]}'}, None),
    ]

    def _fake_generate(config, payload):
        captured_payloads.append(payload)
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        return responses.pop(0)

    monkeypatch.setattr("apd.services.research_execution_ollama._ollama_generate", _fake_generate)
    result = execute_research_brief_ollama_components(db, brief)
    assert result["success"] is True
    assert captured_payloads[-1].get("keep_alive") == 0
    assert not str(captured_payloads[-1].get("prompt", "")).strip()


def test_start_research_ollama_route_uses_mocked_service(client, monkeypatch):
    resp = client.post("/briefs", data={"title": "Web ollama", "research_question": "What is X?"}, follow_redirects=False)
    assert resp.status_code == 303
    brief_id = int(resp.headers["location"].split("/")[-1])

    monkeypatch.setattr(
        "apd.web.routes.get_ollama_execution_config",
        lambda *_args, **_kwargs: (
            type("Cfg", (), {"model": "llama3"})(),
            [],
        ),
    )
    monkeypatch.setattr(
        "apd.web.routes.run_web_research_for_brief",
        lambda db, brief: {
            "success": True,
            "status": "completed",
            "started_at": "2026-01-01T00:00:00+00:00",
            "finished_at": "2026-01-01T00:00:01+00:00",
            "errors": [],
            "warnings": [],
            "proposed_query_count": 1,
            "proposed_url_count": 1,
            "fetched_source_count": 0,
            "queries": [],
            "sources": [],
            "skipped_urls": [],
        },
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


def test_start_research_ollama_components_route_uses_mocked_service(client, monkeypatch):
    resp = client.post("/briefs", data={"title": "Web components", "research_question": "What is X?"}, follow_redirects=False)
    assert resp.status_code == 303
    brief_id = int(resp.headers["location"].split("/")[-1])

    monkeypatch.setattr(
        "apd.web.routes.get_ollama_execution_config",
        lambda *_args, **_kwargs: (
            type("Cfg", (), {"model": "llama3"})(),
            [],
        ),
    )
    monkeypatch.setattr(
        "apd.web.routes.execute_research_brief_ollama_components_grounded",
        lambda db, brief: {
            "success": False,
            "provider": "ollama-components-grounded",
            "model": "llama3",
            "status": "component_validation_failed",
            "started_at": "2026-01-01T00:00:00+00:00",
            "finished_at": "2026-01-01T00:00:01+00:00",
            "errors": ["mocked components failure"],
            "warnings": [],
            "run_id": None,
            "grounding_status": "failed",
            "grounding_errors": ["mocked components failure"],
        },
    )

    resp2 = client.post(f"/briefs/{brief_id}/start-research-ollama-components", follow_redirects=True)
    assert resp2.status_code == 200
    assert "mocked components failure" in resp2.text
    assert "Show raw execution details" in resp2.text


def test_start_research_ollama_route_handles_missing_config(client, monkeypatch):
    resp = client.post("/briefs", data={"title": "Web ollama config", "research_question": "What is X?"}, follow_redirects=False)
    assert resp.status_code == 303
    brief_id = int(resp.headers["location"].split("/")[-1])

    monkeypatch.setattr(
        "apd.web.routes.get_ollama_execution_config",
        lambda *_args, **_kwargs: (None, ["APD_MODEL_PROVIDER=ollama", "APD_OLLAMA_MODEL"]),
    )

    resp2 = client.post(f"/briefs/{brief_id}/start-research-ollama", follow_redirects=True)
    assert resp2.status_code == 200
    assert "Missing required env" in resp2.text
    assert "APD_OLLAMA_MODEL" in resp2.text


def test_stub_route_still_works_when_ollama_path_exists(client):
    resp = client.post("/briefs", data={"title": "Stub still works", "research_question": "What is X?"}, follow_redirects=False)
    assert resp.status_code == 303
    brief_id = int(resp.headers["location"].split("/")[-1])

    resp2 = client.post(f"/briefs/{brief_id}/start-research-stub", follow_redirects=True)
    assert resp2.status_code == 200
    assert "Stub still works" in resp2.text


