"""Tests for research brief creation, listing, detail, and prompt generation."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apd.app.db import Base
from apd.domain.models import ResearchBrief, ResearchBriefStatus
from apd.services.model_execution_settings import save_model_execution_settings
from apd.services.research_brief_ideation import (
    build_brief_ideation_prompt,
    get_brief_ideation_themes,
    parse_generated_brief_idea,
)
from apd.services.research_brief_service import (
    create_brief,
    generate_agent_prompt,
    get_brief,
    list_briefs,
)
from apd.services.sample_research_briefs import get_sample_research_briefs


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def db(tmp_path):
    """Isolated in-memory-style SQLite session."""
    db_path = tmp_path / "test_briefs.db"
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
def client(tmp_path, monkeypatch):
    """TestClient wired to isolated SQLite DB — no fixture seed needed."""
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

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()


# ── Service layer tests ────────────────────────────────────────────────────────


def test_create_brief_minimal(db):
    brief = create_brief(
        db,
        title="Self-hosted ops tools",
        research_question="What pain do solo builders have with self-hosted infrastructure?",
    )
    assert brief.id is not None
    assert brief.title == "Self-hosted ops tools"
    assert brief.status == ResearchBriefStatus.DRAFT
    assert brief.constraints is None
    assert brief.created_at is not None


def test_create_brief_with_all_fields(db):
    brief = create_brief(
        db,
        title="Full brief",
        research_question="Investigate CI/CD pain for small teams.",
        constraints="Exclude enterprise tooling.",
        desired_depth="thorough with evidence links",
        expected_outputs="At least 3 candidates with validation gates.",
        notes="Prior art: Coolify, Dokku.",
    )
    assert brief.title == "Full brief"
    assert brief.constraints == "Exclude enterprise tooling."
    assert brief.desired_depth == "thorough with evidence links"
    assert brief.expected_outputs == "At least 3 candidates with validation gates."
    assert brief.notes == "Prior art: Coolify, Dokku."


def test_list_briefs_returns_most_recent_first(db):
    create_brief(db, title="First", research_question="Q1")
    create_brief(db, title="Second", research_question="Q2")
    briefs = list_briefs(db)
    assert len(briefs) == 2
    # Most recently created should be first
    assert briefs[0].title == "Second"
    assert briefs[1].title == "First"


def test_get_brief_returns_none_for_missing_id(db):
    assert get_brief(db, 9999) is None


def test_get_brief_returns_saved_brief(db):
    created = create_brief(db, title="Find me", research_question="Q?")
    found = get_brief(db, created.id)
    assert found is not None
    assert found.id == created.id
    assert found.title == "Find me"


# ── Prompt generation tests ────────────────────────────────────────────────────


def _make_brief(
    title="Test brief",
    research_question="What pain does segment X have?",
    constraints=None,
    desired_depth=None,
    expected_outputs=None,
    notes=None,
) -> ResearchBrief:
    brief = ResearchBrief(
        title=title,
        research_question=research_question,
        constraints=constraints,
        desired_depth=desired_depth,
        expected_outputs=expected_outputs,
        notes=notes,
        status=ResearchBriefStatus.DRAFT,
    )
    return brief


def test_prompt_includes_research_question():
    brief = _make_brief(research_question="What pain do solo devs face with deploys?")
    prompt = generate_agent_prompt(brief)
    assert "What pain do solo devs face with deploys?" in prompt


def test_prompt_includes_constraints_when_present():
    brief = _make_brief(constraints="Exclude enterprise tools.")
    prompt = generate_agent_prompt(brief)
    assert "Exclude enterprise tools." in prompt


def test_prompt_excludes_constraints_section_when_absent():
    brief = _make_brief()
    prompt = generate_agent_prompt(brief)
    assert "## Constraints" not in prompt


def test_prompt_includes_apd_schema_field_reminders():
    brief = _make_brief()
    prompt = generate_agent_prompt(brief)
    # Key field name reminders must appear
    assert "source_type" in prompt
    assert "excerpt_text" in prompt
    assert "statement" in prompt
    assert "target_type" in prompt
    assert "target_id" in prompt
    assert "relationship" in prompt


def test_prompt_includes_safety_constraints():
    brief = _make_brief()
    prompt = generate_agent_prompt(brief)
    assert "Do not publish externally" in prompt
    assert "create GitHub issues" in prompt
    assert "Do not call external APIs" in prompt


def test_prompt_includes_desired_depth_when_present():
    brief = _make_brief(desired_depth="surface-level overview")
    prompt = generate_agent_prompt(brief)
    assert "surface-level overview" in prompt


def test_prompt_includes_expected_outputs_when_present():
    brief = _make_brief(expected_outputs="3 candidates with validation gates")
    prompt = generate_agent_prompt(brief)
    assert "3 candidates with validation gates" in prompt


def test_prompt_includes_notes_when_present():
    brief = _make_brief(notes="Prior research: Coolify and Dokku.")
    prompt = generate_agent_prompt(brief)
    assert "Coolify and Dokku" in prompt


def test_prompt_references_apd_allowed_phases():
    brief = _make_brief()
    prompt = generate_agent_prompt(brief)
    assert "vague_notion" in prompt
    assert "evidence_collected" in prompt


def test_sample_research_briefs_include_at_least_eight_product_prompts():
    samples = get_sample_research_briefs()
    assert len(samples) >= 8
    for sample in samples:
        question = sample["research_question"]
        assert "Investigate product opportunities" in question
        assert sample["title"].strip()


def test_brief_ideation_themes_include_expected_options():
    themes = get_brief_ideation_themes()
    assert "AI-assisted product research" in themes
    assert "self-hosting and maintenance" in themes
    assert len(themes) >= 8


def test_brief_ideation_prompt_includes_selected_themes():
    prompt = build_brief_ideation_prompt(["AI-assisted product research", "local-first developer tools"])
    assert "AI-assisted product research, local-first developer tools" in prompt
    assert "Return only JSON." in prompt


def test_parse_generated_brief_idea_rejects_researched_source_claims():
    data, ideation_error = parse_generated_brief_idea(
        '{"title":"T","research_question":"Q","notes":"Sources include https://example.com and citations."}'
    )
    assert data is None
    assert ideation_error == "validation_failed: generated_idea_claims_researched_sources"


# ── Web UI tests ───────────────────────────────────────────────────────────────


def test_briefs_list_page_loads_empty(client):
    resp = client.get("/briefs")
    assert resp.status_code == 200
    assert "Research Briefs" in resp.text


def test_briefs_list_page_has_new_brief_link(client):
    resp = client.get("/briefs")
    assert resp.status_code == 200
    assert "/briefs/new" in resp.text


def test_brief_new_page_loads(client):
    resp = client.get("/briefs/new")
    assert resp.status_code == 200
    assert "New Research Brief" in resp.text
    assert "research_question" in resp.text


def test_brief_new_page_shows_randomizer_button_and_helper_text(client):
    resp = client.get("/briefs/new")
    assert resp.status_code == 200
    assert "Randomize brief" in resp.text
    assert "You can edit before saving" in resp.text


def test_brief_new_page_includes_sample_briefs_data(client):
    resp = client.get("/briefs/new")
    assert resp.status_code == 200
    body = resp.text
    assert "sample-briefs-data" in body
    assert "Investigate product opportunities for solo developers who self-host small apps" in body
    assert "Math.random()" in body


def test_brief_new_page_shows_ideation_controls(client):
    resp = client.get("/briefs/new")
    assert resp.status_code == 200
    body = resp.text
    assert "Generate fresh idea" in body
    assert "AI-assisted product research" in body
    assert "self-hosting and maintenance" in body
    assert "Select at least one theme before generating a brief idea." in body


def test_brief_new_page_disables_ideation_when_model_not_configured(client, monkeypatch):
    monkeypatch.delenv("APD_MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("APD_OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("APD_OLLAMA_MODEL", raising=False)

    resp = client.get("/briefs/new")
    assert resp.status_code == 200
    assert "Configure local Ollama model settings to enable fresh idea generation." in resp.text
    assert 'id="generate-brief-idea-btn"' in resp.text
    assert "disabled" in resp.text


def test_brief_ideation_route_returns_config_error_without_model_settings(client, monkeypatch):
    monkeypatch.delenv("APD_MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("APD_OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("APD_OLLAMA_MODEL", raising=False)

    response = client.post("/briefs/ideate", json={"selected_themes": ["AI-assisted product research"]})
    assert response.status_code == 503
    assert response.json()["success"] is False
    assert "not configured" in response.json()["error"].lower()


def test_brief_ideation_route_returns_generated_brief_and_does_not_persist(client):
    import apd.app.db as app_db

    db = app_db.SessionLocal()
    try:
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
        brief_count_before = db.scalar(select(func.count()).select_from(ResearchBrief)) or 0
    finally:
        db.close()

    captured_payloads = []

    def _fake_generate(config, payload):
        captured_payloads.append(payload)
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        return (
            {
                "response": (
                    '{"title":"Fresh idea title","research_question":"Investigate product opportunities for local-first developer tools that reduce deployment friction.",'
                    '"constraints":"Focus on solo builders.","desired_depth":"Thorough with candidates and gates.",'
                    '"expected_outputs":"At least 3 candidate wedges.","notes":"This is a draft idea, not researched output."}'
                )
            },
            None,
        )

    with patch("apd.services.research_brief_ideation._ollama_generate", _fake_generate):
        response = client.post(
            "/briefs/ideate",
            json={"selected_themes": ["AI-assisted product research", "local-first developer tools"]},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["title"] == "Fresh idea title"
    assert any(
        "AI-assisted product research, local-first developer tools" in value.get("prompt", "")
        for value in captured_payloads
    )

    db = app_db.SessionLocal()
    try:
        brief_count_after = db.scalar(select(func.count()).select_from(ResearchBrief)) or 0
    finally:
        db.close()
    assert brief_count_after == brief_count_before


def test_brief_ideation_route_returns_useful_error_for_bad_model_output(client):
    import apd.app.db as app_db

    db = app_db.SessionLocal()
    try:
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
    finally:
        db.close()

    def _fake_generate(config, payload):
        if payload.get("keep_alive") == 0 and not str(payload.get("prompt", "")).strip():
            return ({"response": ""}, None)
        return ({"response": "not json"}, None)

    with patch("apd.services.research_brief_ideation._ollama_generate", _fake_generate):
        response = client.post(
            "/briefs/ideate",
            json={"selected_themes": ["AI-assisted product research"]},
        )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert "parse_failed" in payload["error"]


def test_create_brief_via_post_redirects_to_detail(client):
    resp = client.post(
        "/briefs",
        data={
            "title": "CI/CD pain investigation",
            "research_question": "What frustrates solo devs with CI/CD?",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"].startswith("/briefs/")


def test_brief_detail_page_loads(client):
    # Create via POST then follow redirect
    resp = client.post(
        "/briefs",
        data={
            "title": "Deploy pain",
            "research_question": "What deployment pain exists for solo builders?",
            "constraints": "No enterprise tools.",
            "desired_depth": "thorough",
            "notes": "Check Render, Fly, Coolify.",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    body = resp.text
    assert "Deploy pain" in body
    assert "What deployment pain exists for solo builders?" in body
    assert "No enterprise tools." in body


def test_brief_detail_shows_generated_prompt(client):
    resp = client.post(
        "/briefs",
        data={
            "title": "Ops tooling",
            "research_question": "What ops pain do small teams have?",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    body = resp.text
    assert "Generated agent prompt" in body
    assert "What ops pain do small teams have?" in body
    # Schema reminders should appear in the rendered prompt
    assert "source_type" in body
    assert "excerpt_text" in body


def test_brief_detail_states_apd_not_running_model(client):
    resp = client.post(
        "/briefs",
        data={
            "title": "Market research",
            "research_question": "What tools do indie hackers use for monitoring?",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    # Must clearly say APD is not running the model
    assert "not yet running the model" in resp.text.lower() or "APD is not yet running" in resp.text


def test_brief_detail_shows_future_start_research_disabled(client):
    resp = client.post(
        "/briefs",
        data={
            "title": "Market research",
            "research_question": "What tools do indie hackers use for monitoring?",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    body = resp.text
    assert "Start Research" in body
    # Website-first prototype now exposes Start Research (stub) — it should not be disabled
    assert "not yet available" not in body


def test_brief_list_shows_created_brief(client):
    client.post(
        "/briefs",
        data={"title": "Visible brief", "research_question": "Is this visible?"},
    )
    resp = client.get("/briefs")
    assert resp.status_code == 200
    assert "Visible brief" in resp.text


def test_brief_detail_404_for_missing_brief(client):
    resp = client.get("/briefs/99999")
    assert resp.status_code == 404


def test_runs_page_still_works_after_brief_routes_added(client):
    resp = client.get("/runs")
    assert resp.status_code == 200


def test_nav_links_present_on_runs_page(client):
    resp = client.get("/runs")
    assert resp.status_code == 200
    assert "/briefs" in resp.text


def test_create_brief_with_empty_required_fields_returns_error(client):
    resp = client.post(
        "/briefs",
        data={"title": "", "research_question": ""},
        follow_redirects=False,
    )
    # Should return 422 or redirect back — not 2xx with empty brief created
    assert resp.status_code in (303, 422)
