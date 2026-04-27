from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from apd.app.db import Base
from apd.domain.models import Artifact, Run, Source
from apd.services.legacy_import import import_legacy_run


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_legacy_fixture(root: Path, run_id: str) -> None:
    research_dir = root / "research-corpus" / "runs" / run_id
    artifact_dir = root / "artifacts" / "runs" / run_id

    research_manifest = {
        "run_id": run_id,
        "mode": "test",
        "intent": "Investigate onboarding friction in reviewer workflows",
        "sources": [
            {
                "id": "SRC-001",
                "title": "Forum thread about reviewer bottlenecks",
                "url": "https://example.com/forum/reviewer-bottlenecks",
                "captured_at": "2026-04-20T10:00:00+00:00",
                "source_type": "forum_thread",
                "run_id": run_id,
                "raw_path": f"research-corpus/runs/{run_id}/raw/src-001.html",
                "normalized_path": f"research-corpus/runs/{run_id}/normalized/src-001.md",
                "note_path": f"research-corpus/runs/{run_id}/notes/SRC-001.md",
                "speaker_or_org": "Example Forum",
                "workflow": "reviewer handoff",
                "summary": "Reviewers complain that evidence is scattered across too many files.",
                "why_it_matters": "Signals demand for a reviewer-friendly index.",
                "reliability_notes": "Single public thread; useful but not conclusive.",
            }
        ],
    }
    _write(research_dir / "manifest.json", json.dumps(research_manifest, indent=2))
    _write(
        research_dir / "candidate-links.md",
        "# Candidate Evidence Map\n\n## Candidate: Reviewer Index\n- short thesis: Gather evidence into one review surface.\n",
    )

    artifact_manifest = {
        "run_id": run_id,
        "artifacts": [
            {
                "id": "ART-001",
                "artifact_type": "run_index",
                "path": f"artifacts/runs/{run_id}/run-index.md",
                "created_at": "2026-04-20T11:00:00+00:00",
                "created_by": "legacy-run",
                "inputs": [],
                "purpose": "Reviewer entry point",
                "notes": "",
            }
        ],
    }
    _write(artifact_dir / "manifest.json", json.dumps(artifact_manifest, indent=2))
    _write(
        artifact_dir / "run-index.md",
        "# Run Index\n\n## Run Context\n\n- intent: Investigate onboarding friction in reviewer workflows\n\n## Recommendation Snapshot\n\n- recommended outcome: watch\n",
    )
    _write(
        artifact_dir / "review-package" / "research.md",
        "# Research\n\nReviewers repeatedly say the evidence bundle is difficult to scan quickly.\n",
    )
    _write(
        artifact_dir / "reports" / "discovery-summary.md",
        "# Discovery Summary\n\nLegacy run summary: reviewers need a clearer single-pane review surface.\n",
    )


@pytest.fixture()
def session_factory(tmp_path):
    db_path = tmp_path / "legacy_import.db"
    engine = create_engine(
        f"sqlite+pysqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def test_import_legacy_run_creates_run_sources_and_artifacts(session_factory, tmp_path):
    run_id = "20260422-test-legacy-r1"
    _make_legacy_fixture(tmp_path, run_id)

    with session_factory() as session:
        result = import_legacy_run(session, run_id, repo_root=tmp_path)
        assert result is not None
        assert result.created_run is True
        assert result.imported_source_count == 1
        assert result.linked_artifact_count == 4

        run = session.get(Run, result.run_db_id)
        assert run is not None
        assert run.title == "Test Legacy"
        assert run.source_count == 1

        sources = session.execute(select(Source).where(Source.run_id == run.id)).scalars().all()
        assert len(sources) == 1
        assert sources[0].title == "Forum thread about reviewer bottlenecks"

        artifacts = session.execute(select(Artifact).where(Artifact.run_id == run.id)).scalars().all()
        assert len(artifacts) == 4
        assert any(a.path.endswith("candidate-links.md") for a in artifacts)
        assert any(a.path.endswith("run-index.md") for a in artifacts)


def test_import_legacy_run_is_idempotent(session_factory, tmp_path):
    run_id = "20260422-test-legacy-r2"
    _make_legacy_fixture(tmp_path, run_id)

    with session_factory() as session:
        first = import_legacy_run(session, run_id, repo_root=tmp_path)
        second = import_legacy_run(session, run_id, repo_root=tmp_path)
        assert first is not None
        assert second is not None
        assert second.created_run is False

        runs = session.execute(select(Run)).scalars().all()
        sources = session.execute(select(Source)).scalars().all()
        artifacts = session.execute(select(Artifact)).scalars().all()
        assert len(runs) == 1
        assert len(sources) == 1
        assert len(artifacts) == 4


def test_import_legacy_run_warns_but_continues_for_missing_files(session_factory, tmp_path):
    run_id = "20260422-warning-legacy-r1"
    research_dir = tmp_path / "research-corpus" / "runs" / run_id
    artifact_dir = tmp_path / "artifacts" / "runs" / run_id
    _write(research_dir / "manifest.json", json.dumps({"run_id": run_id, "sources": []}, indent=2))
    _write(artifact_dir / "run-index.md", "# Run Index\n\n## Run Context\n\n- intent: warning path\n")

    with session_factory() as session:
        result = import_legacy_run(session, run_id, repo_root=tmp_path)
        assert result is not None
        assert result.run_db_id > 0
        assert result.warnings
        assert any("missing artifact manifest" in warning for warning in result.warnings)


def test_imported_legacy_run_appears_in_ui(session_factory, tmp_path, monkeypatch):
    run_id = "20260422-ui-legacy-r1"
    _make_legacy_fixture(tmp_path, run_id)

    with session_factory() as session:
        result = import_legacy_run(session, run_id, repo_root=tmp_path)
        assert result is not None
        db_run_id = result.run_db_id

    import apd.app.db as app_db
    import apd.web.routes as web_routes

    monkeypatch.setattr(app_db, "SessionLocal", session_factory)

    def _override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    from apd.app.main import app

    app.dependency_overrides[web_routes._get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as client:
        runs_page = client.get("/runs")
        assert runs_page.status_code == 200
        assert "Ui Legacy" in runs_page.text

        detail_page = client.get(f"/runs/{db_run_id}")
        assert detail_page.status_code == 200
        assert "Forum thread about reviewer bottlenecks" in detail_page.text
        assert "candidate-links.md" in detail_page.text

    app.dependency_overrides.clear()
