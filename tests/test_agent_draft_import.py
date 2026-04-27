from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from apd.app.db import Base
from apd.domain.models import Candidate, Claim, EvidenceLink, ReviewStatus, Run, Theme, ValidationGate
from apd.services.agent_draft_import import (
    AgentDraftValidationError,
    DuplicateExternalDraftIdError,
    import_agent_draft_file,
)
from apd.services.report_export import export_run_markdown_report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sample_package(external_draft_id: str = "draft-abc") -> dict:
    return {
        "schema_version": "1.0",
        "external_draft_id": external_draft_id,
        "agent_name": "test-agent",
        "run": {
            "title": "Draft Import Test Run",
            "intent": "Validate agent draft import path",
            "summary": "Draft data for tests",
            "mode": "agent_draft",
            "phase": "evidence_collected",
            "recommendation": "Watch"
        },
        "sources": [
            {
                "id": "src-1",
                "title": "Source One",
                "source_type": "note",
                "summary": "Source summary"
            }
        ],
        "evidence_excerpts": [
            {
                "id": "ex-1",
                "source_id": "src-1",
                "excerpt_text": "This is supporting evidence.",
                "location_reference": "note-1"
            }
        ],
        "claims": [
            {
                "id": "claim-1",
                "statement": "Teams lose time to fragmented recruiting updates.",
                "claim_type": "pain"
            }
        ],
        "themes": [
            {
                "id": "theme-1",
                "name": "Fragmented workflows",
                "summary": "Coordination is spread across tools"
            }
        ],
        "candidates": [
            {
                "id": "cand-1",
                "title": "Recruiting Sync Ledger",
                "summary": "One workflow for candidate state",
                "target_user": "Recruiters",
                "first_workflow": "Interview handoff",
                "first_wedge": "Single source of truth"
            }
        ],
        "validation_gates": [
            {
                "id": "gate-1",
                "candidate_id": "cand-1",
                "name": "Validate buyer urgency",
                "description": "Interview three buyer-side operators",
                "status": "not_started",
                "missing_evidence": "No direct buyer interviews yet"
            }
        ],
        "evidence_links": [
            {
                "id": "link-claim",
                "source_id": "src-1",
                "excerpt_id": "ex-1",
                "target_type": "claim",
                "target_id": "claim-1",
                "relationship": "supports",
                "strength": "medium"
            },
            {
                "id": "link-theme",
                "source_id": "src-1",
                "excerpt_id": "ex-1",
                "target_type": "theme",
                "target_id": "theme-1",
                "relationship": "example_of"
            },
            {
                "id": "link-candidate",
                "source_id": "src-1",
                "excerpt_id": "ex-1",
                "target_type": "candidate",
                "target_id": "cand-1",
                "relationship": "supports"
            },
            {
                "id": "link-gate",
                "source_id": "src-1",
                "excerpt_id": "ex-1",
                "target_type": "validation_gate",
                "target_id": "gate-1",
                "relationship": "context_for"
            }
        ]
    }


@pytest.fixture()
def session_factory(tmp_path):
    db_path = tmp_path / "test_agent_draft.db"
    engine = create_engine(
        f"sqlite+pysqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def test_import_agent_draft_success(session_factory, tmp_path):
    draft_path = tmp_path / "draft.json"
    _write_json(draft_path, _sample_package())

    with session_factory() as session:
        result = import_agent_draft_file(session, draft_path)
        run = session.get(Run, result.run_db_id)

        assert run is not None
        assert run.source_count == 1
        assert run.claim_count == 1
        assert run.theme_count == 1
        assert run.candidate_count == 1

        claims = session.execute(select(Claim).where(Claim.run_id == run.id)).scalars().all()
        themes = session.execute(select(Theme).where(Theme.run_id == run.id)).scalars().all()
        candidates = session.execute(select(Candidate).where(Candidate.run_id == run.id)).scalars().all()

        assert claims[0].review_status == ReviewStatus.UNREVIEWED
        assert claims[0].is_agent_generated is True
        assert themes[0].review_status == ReviewStatus.UNREVIEWED
        assert candidates[0].review_status == ReviewStatus.UNREVIEWED
        assert candidates[0].is_agent_generated is True

        links = session.execute(select(EvidenceLink).where(EvidenceLink.run_id == run.id)).scalars().all()
        assert len(links) == 4
        assert {str(link.target_type) for link in links} == {
            "claim",
            "theme",
            "candidate",
            "validation_gate",
        }


def test_import_agent_draft_rejects_malformed_package(session_factory, tmp_path):
    invalid_path = tmp_path / "invalid.json"
    _write_json(
        invalid_path,
        {
            "schema_version": "1.0",
            "run": {
                "summary": "Missing title and intent"
            },
            "sources": [],
            "claims": [],
            "candidates": [],
        },
    )

    with session_factory() as session:
        with pytest.raises(AgentDraftValidationError) as exc_info:
            import_agent_draft_file(session, invalid_path)

    error_text = "\n".join(exc_info.value.errors)
    assert "run.title or run.intent is required" in error_text


def test_import_agent_draft_duplicate_external_id_behavior(session_factory, tmp_path):
    draft_path = tmp_path / "draft.json"
    _write_json(draft_path, _sample_package(external_draft_id="duplicate-id"))

    with session_factory() as session:
        first = import_agent_draft_file(session, draft_path)
        assert first.run_db_id > 0

        with pytest.raises(DuplicateExternalDraftIdError):
            import_agent_draft_file(session, draft_path)

        second = import_agent_draft_file(
            session,
            draft_path,
            allow_duplicate_external_id=True,
        )
        assert second.run_db_id != first.run_db_id


def test_imported_draft_visible_in_ui_and_report(session_factory, tmp_path, monkeypatch):
    draft_path = tmp_path / "draft.json"
    _write_json(draft_path, _sample_package(external_draft_id="ui-path"))

    with session_factory() as session:
        result = import_agent_draft_file(session, draft_path)
        db_run_id = result.run_db_id

    import apd.app.db as app_db
    import apd.web.routes as web_routes

    monkeypatch.setattr(app_db, "SessionLocal", session_factory)

    def _override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    from apd.app.main import app

    app.dependency_overrides[web_routes._get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as client:
        runs_page = client.get("/runs")
        assert runs_page.status_code == 200
        assert "Draft Import Test Run" in runs_page.text

        detail_page = client.get(f"/runs/{db_run_id}")
        assert detail_page.status_code == 200
        assert "Source One" in detail_page.text
        assert "Fragmented workflows" in detail_page.text
        assert "Recruiting Sync Ledger" in detail_page.text
        assert "Validate buyer urgency" in detail_page.text
        assert "supports" in detail_page.text
        assert "context_for" in detail_page.text

    app.dependency_overrides.clear()

    with session_factory() as session:
        export = export_run_markdown_report(session, db_run_id, export_root=tmp_path / "exports")
        assert export is not None
        report = export.artifact_path.read_text(encoding="utf-8")
        assert "Draft Import Test Run" in report
        assert "## Sources" in report
        assert "## Claims" in report
        assert "## Themes" in report
        assert "## Candidates" in report
        assert "## Validation Gates And Gaps" in report
        assert "supports" in report
