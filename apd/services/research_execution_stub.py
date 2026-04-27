from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pathlib import Path

from sqlalchemy.orm import Session

from apd.services.research_brief_service import get_brief
from apd.services.agent_draft_validation import validate_agent_draft_data
from apd.services.agent_draft_import import import_agent_draft_package, AgentDraftPackage


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_stub_package_dict(brief) -> dict[str, Any]:
    now = _iso_now()
    external_id = f"brief-{brief.id}-{now}"
    run_title = brief.title or (brief.research_question[:120] if brief.research_question else "Stub Research")
    run_intent = brief.research_question
    package = {
        "schema_version": "1.0",
        "external_draft_id": external_id,
        "agent_name": "apd-stub-runner",
        "generated_at": now,
        "run": {
            "title": run_title,
            "intent": run_intent,
            "summary": "This is deterministic stub output for website-first execution prototype. Not real research.",
            "mode": "stub_research_execution",
            "phase": "evidence_collected",
            "recommendation": "needs_human_review",
        },
        "warnings": ["This is deterministic stub output, not real research."],
        "limitations": ["No model call, no source fetching, no external research performed."],
        "sources": [
            {
                "id": "src-1",
                "title": "Stub source for brief",
                "source_type": "stub",
                "url": None,
                "origin": "apd-stub-runner",
                "metadata_json": {"brief_id": brief.id},
            }
        ],
        "evidence_excerpts": [
            {"id": "ex-1", "source_id": "src-1", "excerpt_text": "Stub excerpt text generated from brief."}
        ],
        "claims": [
            {"id": "claim-1", "statement": "Stub claim derived from brief."}
        ],
        "themes": [
            {"id": "theme-1", "name": "Stub theme"}
        ],
        "candidates": [
            {"id": "cand-1", "title": "Stub candidate", "summary": "A synthetic candidate produced by the stub runner."}
        ],
        "validation_gates": [
            {"id": "gate-1", "candidate_id": "cand-1", "phase": "evidence_collected", "name": "Stub validation gate"}
        ],
        "evidence_links": [
            {"id": "link-1", "source_id": "src-1", "excerpt_id": "ex-1", "target_type": "claim", "target_id": "claim-1", "relationship": "supports", "strength": "medium"},
            {"id": "link-2", "source_id": "src-1", "excerpt_id": "ex-1", "target_type": "theme", "target_id": "theme-1", "relationship": "example_of", "strength": "weak"},
            {"id": "link-3", "source_id": "src-1", "excerpt_id": "ex-1", "target_type": "candidate", "target_id": "cand-1", "relationship": "supports", "strength": "medium"},
            {"id": "link-4", "source_id": "src-1", "excerpt_id": "ex-1", "target_type": "validation_gate", "target_id": "gate-1", "relationship": "context_for", "strength": "weak"},
        ],
    }
    return package


def execute_research_brief_stub(db: Session, brief) -> dict[str, Any]:
    """Build a deterministic stub package, validate it, import it, and return import result.

    Returns a dict with keys: success (bool), message (str), run_id (int|None).
    """
    package_dict = build_stub_package_dict(brief)

    # Validate using in-memory data (path used only for reporting)
    report = validate_agent_draft_data(Path("<stub>"), package_dict)
    if not report.is_valid or report.package is None:
        return {"success": False, "message": "Validation failed", "errors": report.errors}

    # Import using the already-validated package model
    try:
        result = import_agent_draft_package(db, report.package, package_path=None, allow_duplicate_external_id=False)
    except Exception as exc:
        return {"success": False, "message": f"Import failed: {exc}", "errors": [str(exc)]}

    return {"success": True, "message": "Imported", "run_id": result.run_db_id, "warnings": result.warnings}
