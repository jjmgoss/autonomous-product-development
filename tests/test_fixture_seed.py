from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from apd.app.db import Base
from apd.domain.models import Artifact
from apd.domain.models import Candidate
from apd.domain.models import Claim
from apd.domain.models import Decision
from apd.domain.models import EvidenceExcerpt
from apd.domain.models import EvidenceLink
from apd.domain.models import ReviewNote
from apd.domain.models import Run
from apd.domain.models import Source
from apd.domain.models import Theme
from apd.domain.models import ValidationGate
from apd.fixtures.seed import seed_fixture_data


def _count(session: Session, model) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_fixture_seed_creates_expected_graph(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'fixture_seed.db'}", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        result = seed_fixture_data(session)
        session.commit()

        assert result.created is True
        assert result.run_count == 1
        assert result.source_count >= 3
        assert result.excerpt_count >= 6
        assert result.claim_count >= 5
        assert result.theme_count >= 2
        assert result.candidate_count >= 2
        assert result.evidence_link_count >= 1
        assert result.validation_gate_count >= 1
        assert result.decision_count >= 1
        assert result.artifact_count >= 1

        assert _count(session, Run) == 1
        assert _count(session, Source) >= 3
        assert _count(session, EvidenceExcerpt) >= 6
        assert _count(session, Claim) >= 5
        assert _count(session, Theme) >= 2
        assert _count(session, Candidate) >= 2
        assert _count(session, EvidenceLink) >= 1
        assert _count(session, ValidationGate) >= 1
        assert _count(session, ReviewNote) >= 1
        assert _count(session, Decision) >= 1
        assert _count(session, Artifact) >= 1


def test_fixture_seed_is_idempotent_and_resettable(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'fixture_idempotent.db'}", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        first = seed_fixture_data(session)
        session.commit()

        second = seed_fixture_data(session)
        session.commit()

        assert first.created is True
        assert second.created is False
        assert second.run_count == 1
        assert _count(session, Run) == 1

        third = seed_fixture_data(session, reset_fixture=True)
        session.commit()

        assert third.created is True
        assert _count(session, Run) == 1
        assert _count(session, Source) == third.source_count
        assert _count(session, EvidenceExcerpt) == third.excerpt_count
        assert _count(session, Claim) == third.claim_count


def test_fixture_reset_does_not_delete_user_runs(tmp_path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'fixture_reset_scope.db'}", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_fixture_data(session)
        session.add(Run(title="User-created local run", mode="manual"))
        session.commit()

        reseed = seed_fixture_data(session, reset_fixture=True)
        session.commit()

        assert reseed.created is True
        assert _count(session, Run) == 2
        user_run = session.scalar(select(Run).where(Run.title == "User-created local run"))
        assert user_run is not None
