from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from apd.app.db import Base
from apd.domain.models import Run
from apd.services.agent_draft_validation import validate_agent_draft_file


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PACKAGE = ROOT / "apd" / "fixtures" / "examples" / "agent_draft_sample.json"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _near_miss_package() -> dict:
    return {
        "schema_version": "1.0",
        "external_draft_id": "draft-near-miss",
        "agent_name": "test-agent",
        "run": {
            "title": "Near miss package",
            "intent": "Exercise repair hints",
            "summary": "Contains common near-miss fields",
        },
        "sources": [
            {
                "id": "src-1",
                "title": "Source One",
                "type": "note",
                "accessed_at": "2026-04-26T18:20:00Z",
                "extra_note": "keep me",
            }
        ],
        "evidence_excerpts": [
            {
                "id": "ex-1",
                "source_id": "src-1",
                "text": "Support text",
                "locator": "note-1",
            }
        ],
        "claims": [
            {
                "id": "claim-1",
                "claim": "Claim text",
                "confidence": "0.65",
            }
        ],
        "themes": [
            {
                "id": "theme-1",
                "theme": "Theme title",
            }
        ],
        "candidates": [
            {
                "id": "cand-1",
                "name": "Candidate name",
                "description": "Candidate summary",
            }
        ],
        "validation_gates": [
            {
                "id": "gate-1",
                "candidate_id": "cand-1",
                "phase": "problem_validation",
                "name": "Validate urgency",
            }
        ],
        "evidence_links": [
            {
                "id": "link-1",
                "source_id": "src-1",
                "excerpt_id": "ex-1",
                "claim_id": "claim-1",
            },
            {
                "id": "link-2",
                "source_id": "src-1",
                "excerpt_id": "ex-1",
                "theme_id": "theme-1",
                "relationship": "example_of",
            },
            {
                "id": "link-3",
                "source_id": "src-1",
                "excerpt_id": "ex-1",
                "candidate_id": "cand-1",
                "relationship": "supports",
            },
            {
                "id": "link-4",
                "source_id": "src-1",
                "excerpt_id": "ex-1",
                "gate_id": "gate-1",
                "relationship": "context_for",
            },
        ],
    }


def test_validate_agent_draft_sample_package_passes() -> None:
    report = validate_agent_draft_file(SAMPLE_PACKAGE)
    assert report.is_valid is True
    assert report.error_count == 0
    assert report.grouped_errors == []


def test_validate_agent_draft_handles_utf8_bom(tmp_path) -> None:
    bom_sample = tmp_path / "sample-with-bom.json"
    payload = SAMPLE_PACKAGE.read_text(encoding="utf-8")
    bom_sample.write_text(payload, encoding="utf-8-sig")

    report = validate_agent_draft_file(bom_sample)

    assert report.is_valid is True
    assert report.error_count == 0


def test_validate_agent_draft_invalid_package_outputs_actionable_hints(tmp_path) -> None:
    near_miss_path = tmp_path / "near-miss.json"
    _write_json(near_miss_path, _near_miss_package())

    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_agent_draft.py",
            "--path",
            str(near_miss_path),
            "--repair-hints",
            "--repair-prompt",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "valid=false" in result.stdout
    assert "ISSUE: sources: rename type -> source_type" in result.stdout
    assert "ISSUE: evidence_links: replace legacy target fields" in result.stdout
    assert "HINT: In claims, rename claim to statement." in result.stdout
    assert "HINT: Map validation_gates.phase problem_validation to supported_opportunity." in result.stdout
    assert "REPAIR_PROMPT_BEGIN" in result.stdout
    assert "Return only JSON." in result.stdout


def test_validate_agent_draft_does_not_write_database(tmp_path) -> None:
    db_path = tmp_path / "validate_only.db"
    engine = create_engine(
        f"sqlite+pysqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_agent_draft.py",
            "--path",
            str(SAMPLE_PACKAGE),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "APD_DATABASE_URL": f"sqlite+pysqlite:///{db_path}"},
    )

    assert result.returncode == 0
    with Session(engine) as session:
        run_count = session.scalar(select(func.count()).select_from(Run))
        assert run_count == 0


def test_normalize_agent_draft_repairs_common_near_misses(tmp_path) -> None:
    near_miss_path = tmp_path / "near-miss.json"
    normalized_path = tmp_path / "near-miss.normalized.json"
    payload = _near_miss_package()
    payload["evidence_links"][0]["relationship"] = "supports"
    _write_json(near_miss_path, payload)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/normalize_agent_draft.py",
            "--path",
            str(near_miss_path),
            "--out",
            str(normalized_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert normalized_path.exists()
    assert "applied_fixes=" in result.stdout
    report = validate_agent_draft_file(normalized_path)
    assert report.is_valid is True
