"""Tests for issue #8: human review controls and run decision updates."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from apd.app.db import Base
from apd.domain.models import Candidate, Claim, Decision, ReviewNote
from apd.fixtures.seed import seed_fixture_data


@pytest.fixture()
def client_and_session(tmp_path, monkeypatch):
    """Return (TestClient, TestSession) wired to an isolated SQLite DB with fixture data."""
    db_path = tmp_path / "test_review.db"
    db_url = f"sqlite+pysqlite:///{db_path}"

    test_engine = create_engine(db_url, future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    with TestSession() as session:
        seed_fixture_data(session)
        session.commit()

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
    app.dependency_overrides[web_routes._get_db] = _override_get_db

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, TestSession

    app.dependency_overrides.clear()


@pytest.fixture()
def client(client_and_session):
    c, _ = client_and_session
    return c


@pytest.fixture()
def db(client_and_session):
    _, SessionCls = client_and_session
    with SessionCls() as session:
        yield session


# --- helper to get the first claim/candidate id from fixture data ---

def _first_claim_id(db) -> int:
    return db.execute(select(Claim).limit(1)).scalars().first().id


def _first_candidate_id(db) -> int:
    return db.execute(select(Candidate).limit(1)).scalars().first().id


# --- claim review ---

def test_update_claim_review_status_persists(client_and_session):
    c, SessionCls = client_and_session
    with SessionCls() as db:
        claim_id = _first_claim_id(db)

    resp = c.post(
        f"/runs/1/claims/{claim_id}/review",
        data={"review_status": "accepted", "note": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    with SessionCls() as db:
        claim = db.get(Claim, claim_id)
        assert str(claim.review_status) == "accepted"


def test_update_claim_review_creates_note(client_and_session):
    c, SessionCls = client_and_session
    with SessionCls() as db:
        claim_id = _first_claim_id(db)
        initial_notes = db.execute(
            select(ReviewNote).where(ReviewNote.target_id == claim_id)
        ).scalars().all()
        initial_count = len(initial_notes)

    resp = c.post(
        f"/runs/1/claims/{claim_id}/review",
        data={"review_status": "weak", "note": "Needs more evidence"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    with SessionCls() as db:
        notes = db.execute(
            select(ReviewNote).where(ReviewNote.target_id == claim_id)
        ).scalars().all()
        assert len(notes) == initial_count + 1
        latest = notes[-1]
        assert latest.note == "Needs more evidence"


def test_update_claim_review_no_note_no_extra_record(client_and_session):
    c, SessionCls = client_and_session
    with SessionCls() as db:
        claim_id = _first_claim_id(db)
        initial_count = len(
            db.execute(select(ReviewNote).where(ReviewNote.target_id == claim_id)).scalars().all()
        )

    resp = c.post(
        f"/runs/1/claims/{claim_id}/review",
        data={"review_status": "disputed", "note": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    with SessionCls() as db:
        count_after = len(
            db.execute(select(ReviewNote).where(ReviewNote.target_id == claim_id)).scalars().all()
        )
        assert count_after == initial_count


def test_invalid_review_status_rejected(client):
    resp = client.post(
        "/runs/1/claims/1/review",
        data={"review_status": "nonsense_value", "note": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 422


def test_claim_review_wrong_run_returns_404(client_and_session):
    c, SessionCls = client_and_session
    with SessionCls() as db:
        claim_id = _first_claim_id(db)

    resp = c.post(
        f"/runs/9999/claims/{claim_id}/review",
        data={"review_status": "accepted", "note": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 404


# --- candidate review ---

def test_update_candidate_review_status_persists(client_and_session):
    c, SessionCls = client_and_session
    with SessionCls() as db:
        candidate_id = _first_candidate_id(db)

    resp = c.post(
        f"/runs/1/candidates/{candidate_id}/review",
        data={"review_status": "accepted", "note": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    with SessionCls() as db:
        candidate = db.get(Candidate, candidate_id)
        assert str(candidate.review_status) == "accepted"


def test_update_candidate_review_creates_note(client_and_session):
    c, SessionCls = client_and_session
    with SessionCls() as db:
        candidate_id = _first_candidate_id(db)
        initial_count = len(
            db.execute(select(ReviewNote).where(ReviewNote.target_id == candidate_id)).scalars().all()
        )

    resp = c.post(
        f"/runs/1/candidates/{candidate_id}/review",
        data={"review_status": "needs_followup", "note": "Need pricing data"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    with SessionCls() as db:
        notes = db.execute(
            select(ReviewNote).where(ReviewNote.target_id == candidate_id)
        ).scalars().all()
        assert len(notes) == initial_count + 1
        assert notes[-1].note == "Need pricing data"


# --- standalone note endpoints ---

def test_add_claim_note_standalone(client_and_session):
    c, SessionCls = client_and_session
    with SessionCls() as db:
        claim_id = _first_claim_id(db)

    resp = c.post(
        f"/runs/1/claims/{claim_id}/notes",
        data={"note": "Follow-up needed on this point"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    with SessionCls() as db:
        notes = db.execute(
            select(ReviewNote).where(ReviewNote.target_id == claim_id)
        ).scalars().all()
        assert any(n.note == "Follow-up needed on this point" for n in notes)


def test_add_candidate_note_standalone(client_and_session):
    c, SessionCls = client_and_session
    with SessionCls() as db:
        candidate_id = _first_candidate_id(db)

    resp = c.post(
        f"/runs/1/candidates/{candidate_id}/notes",
        data={"note": "Strong candidate for pilot"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    with SessionCls() as db:
        notes = db.execute(
            select(ReviewNote).where(ReviewNote.target_id == candidate_id)
        ).scalars().all()
        assert any(n.note == "Strong candidate for pilot" for n in notes)


def test_add_claim_note_empty_text_rejected(client_and_session):
    c, SessionCls = client_and_session
    with SessionCls() as db:
        claim_id = _first_claim_id(db)

    resp = c.post(
        f"/runs/1/claims/{claim_id}/notes",
        data={"note": "   "},
        follow_redirects=False,
    )
    assert resp.status_code == 422


# --- run decision ---

def test_update_run_decision_persists(client_and_session):
    c, SessionCls = client_and_session

    resp = c.post(
        "/runs/1/decision",
        data={"decision": "watch", "rationale": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # After redirect, GET /runs/1 should show the new decision
    resp2 = c.get("/runs/1")
    assert resp2.status_code == 200
    assert "watch" in resp2.text


def test_update_run_decision_creates_history_record(client_and_session):
    c, SessionCls = client_and_session
    with SessionCls() as db:
        initial_count = len(
            db.execute(select(Decision).where(Decision.run_id == 1)).scalars().all()
        )

    resp = c.post(
        "/runs/1/decision",
        data={"decision": "publish", "rationale": "Meets all gates"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    with SessionCls() as db:
        decisions = db.execute(
            select(Decision).where(Decision.run_id == 1)
        ).scalars().all()
        assert len(decisions) == initial_count + 1
        latest = decisions[-1]
        assert str(latest.decision) == "publish"
        assert latest.rationale == "Meets all gates"


def test_update_run_decision_visible_on_recent_runs(client_and_session):
    c, SessionCls = client_and_session

    resp = c.post(
        "/runs/1/decision",
        data={"decision": "archive", "rationale": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    resp2 = c.get("/runs")
    assert resp2.status_code == 200
    assert "archive" in resp2.text


def test_build_approved_can_be_explicitly_set(client_and_session):
    """build_approved requires an explicit human selection — verify it can be saved."""
    c, SessionCls = client_and_session

    resp = c.post(
        "/runs/1/decision",
        data={"decision": "build_approved", "rationale": "Reviewed and approved"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    resp2 = c.get("/runs/1")
    assert resp2.status_code == 200
    assert "build" in resp2.text


def test_invalid_decision_value_rejected(client):
    resp = client.post(
        "/runs/1/decision",
        data={"decision": "do_nothing_ever", "rationale": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 422


def test_review_does_not_delete_claims(client_and_session):
    """Updating a claim review must not delete or hide the claim from the detail page."""
    c, SessionCls = client_and_session
    with SessionCls() as db:
        claim_id = _first_claim_id(db)
        original_statement = db.get(Claim, claim_id).statement

    c.post(
        f"/runs/1/claims/{claim_id}/review",
        data={"review_status": "disputed", "note": ""},
        follow_redirects=False,
    )

    resp = c.get("/runs/1")
    assert resp.status_code == 200
    # Claim statement still appears on the detail page
    assert original_statement[:30] in resp.text


def test_run_detail_shows_review_forms(client):
    """run_detail page should contain form elements for review."""
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    body = resp.text
    assert 'method="post"' in body
    assert "review_status" in body
    assert "Update Run Decision" in body
