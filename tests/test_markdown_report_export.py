from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from apd.app.db import Base
from apd.domain.models import Artifact
from apd.fixtures.seed import seed_fixture_data
from apd.services.report_export import export_run_markdown_report, render_run_report_markdown
from apd.web.queries import get_run_detail


@pytest.fixture()
def session_factory(tmp_path):
    db_path = tmp_path / "test_export.db"
    db_url = f"sqlite+pysqlite:///{db_path}"

    engine = create_engine(db_url, future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionCls = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionCls() as session:
        seed_fixture_data(session)
        session.commit()

    return SessionCls


@pytest.fixture()
def db(session_factory):
    with session_factory() as session:
        yield session


def test_render_fixture_report_includes_required_sections(db):
    detail = get_run_detail(db, 1)
    assert detail is not None

    report = render_run_report_markdown(detail)

    assert "# Fixture Demo: Solo builders deploying self-hosted apps" in report
    assert "## Intent" in report
    assert "## Summary" in report
    assert "## Recommendation" in report
    assert "## Run State" in report
    assert "## Decision History" in report
    assert "## Sources" in report
    assert "## Claims" in report
    assert "### Accepted" in report
    assert "### Weak" in report
    assert "### Disputed" in report
    assert "### Unreviewed" in report
    assert "## Themes" in report
    assert "## Candidates" in report
    assert "## Validation Gates And Gaps" in report
    assert "## Review Notes" in report
    assert "## Known Weak, Disputed, Or Needs-Followup Material" in report
    assert "evidence:" in report
    assert "source#" in report


def test_export_creates_file_and_artifact(db, tmp_path):
    export_root = tmp_path / "exports"

    result = export_run_markdown_report(db, 1, export_root=export_root)
    assert result is not None
    assert result.artifact_path.exists()
    assert result.artifact_path.suffix == ".md"

    artifact = db.get(Artifact, result.artifact_id)
    assert artifact is not None
    assert artifact.run_id == 1
    assert artifact.artifact_type == "markdown_report"
    assert artifact.path is not None
    assert "run-1-report-" in artifact.path

    body = result.artifact_path.read_text(encoding="utf-8")
    assert "## Sources" in body
    assert "## Claims" in body
    assert "## Themes" in body
    assert "## Candidates" in body
    assert "## Validation Gates And Gaps" in body


def test_repeated_export_does_not_silently_clobber(db, tmp_path):
    export_root = tmp_path / "exports"

    first = export_run_markdown_report(db, 1, export_root=export_root)
    second = export_run_markdown_report(db, 1, export_root=export_root)

    assert first is not None
    assert second is not None
    assert first.artifact_path != second.artifact_path
    assert first.artifact_path.exists()
    assert second.artifact_path.exists()

    exported_artifacts = db.execute(
        select(Artifact).where(Artifact.run_id == 1, Artifact.artifact_type == "markdown_report")
    ).scalars().all()
    assert len(exported_artifacts) == 2


@pytest.fixture()
def client_and_session(session_factory, monkeypatch, tmp_path):
    import apd.app.db as app_db
    import apd.services.report_export as report_export_service
    import apd.web.routes as web_routes

    export_root = tmp_path / "route_exports"

    monkeypatch.setattr(app_db, "SessionLocal", session_factory)

    def _override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    original_export = report_export_service.export_run_markdown_report

    def _export_with_tmp_root(db, run_id):
        return original_export(db, run_id, export_root=export_root)

    monkeypatch.setattr(web_routes, "export_run_markdown_report", _export_with_tmp_root)

    from apd.app.main import app

    app.dependency_overrides[web_routes._get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, session_factory
    app.dependency_overrides.clear()


def test_export_report_route_creates_artifact_and_redirects(client_and_session):
    client, SessionCls = client_and_session

    response = client.post("/runs/1/export-report", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith("/runs/1#artifacts")

    with SessionCls() as session:
        exported_artifacts = session.execute(
            select(Artifact).where(Artifact.run_id == 1, Artifact.artifact_type == "markdown_report")
        ).scalars().all()
        assert len(exported_artifacts) == 1
        path = exported_artifacts[0].path
        assert path is not None
        candidate = Path(path)
        if candidate.is_absolute():
            resolved = candidate
        else:
            resolved = Path(__file__).resolve().parents[1] / candidate
        assert resolved.exists()
