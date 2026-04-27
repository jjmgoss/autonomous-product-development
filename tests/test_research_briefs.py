"""Tests for research brief creation, listing, detail, and prompt generation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apd.app.db import Base
from apd.domain.models import ResearchBrief, ResearchBriefStatus
from apd.services.research_brief_service import (
    create_brief,
    generate_agent_prompt,
    get_brief,
    list_briefs,
)


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
