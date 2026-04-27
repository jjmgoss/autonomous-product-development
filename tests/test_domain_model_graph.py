from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from apd.app.db import Base
from apd.domain.models import Artifact
from apd.domain.models import Candidate
from apd.domain.models import Claim
from apd.domain.models import Decision
from apd.domain.models import DecisionTargetType
from apd.domain.models import DecisionValue
from apd.domain.models import EvidenceExcerpt
from apd.domain.models import EvidenceLink
from apd.domain.models import EvidenceRelationship
from apd.domain.models import EvidenceTargetType
from apd.domain.models import ReviewNote
from apd.domain.models import ReviewStatus
from apd.domain.models import ReviewTargetType
from apd.domain.models import Run
from apd.domain.models import RunPhase
from apd.domain.models import Source
from apd.domain.models import Theme
from apd.domain.models import ValidationGate
from apd.domain.models import ValidationGateStatus


def _engine_for(tmp_path):
    return create_engine(f"sqlite+pysqlite:///{tmp_path / 'model_graph.db'}", future=True)


def test_minimal_research_run_graph(tmp_path) -> None:
    engine = _engine_for(tmp_path)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        run = Run(
            title="Customer support handoff bottleneck",
            intent="Understand repeated pain in support escalation workflows",
            phase=RunPhase.EVIDENCE_COLLECTED,
        )
        session.add(run)
        session.flush()

        source = Source(
            run_id=run.id,
            source_type="url",
            title="Community thread",
            url="https://example.com/thread/1",
        )
        session.add(source)
        session.flush()

        excerpt = EvidenceExcerpt(
            run_id=run.id,
            source_id=source.id,
            excerpt_text="We lose context every time support escalates to engineering.",
            excerpt_type="complaint",
        )
        session.add(excerpt)

        claim = Claim(
            run_id=run.id,
            statement="Escalation context loss creates repeated customer frustration.",
            claim_type="pain",
            created_by="agent",
            is_agent_generated=True,
        )
        session.add(claim)
        session.flush()

        theme = Theme(
            run_id=run.id,
            name="Escalation context loss",
            summary="Critical data is dropped between teams.",
        )
        session.add(theme)

        candidate = Candidate(
            run_id=run.id,
            title="Support-to-engineering handoff brief",
            summary="Generate a compact handoff packet before escalation.",
            first_workflow="Tier-1 to engineering escalation",
            first_wedge="Auto-compiled issue context",
            is_agent_generated=True,
        )
        session.add(candidate)
        session.flush()

        link = EvidenceLink(
            run_id=run.id,
            source_id=source.id,
            excerpt_id=excerpt.id,
            target_type=EvidenceTargetType.CLAIM,
            target_id=claim.id,
            relationship_type=EvidenceRelationship.SUPPORTS,
        )
        session.add(link)

        gate = ValidationGate(
            run_id=run.id,
            candidate_id=candidate.id,
            phase=RunPhase.SUPPORTED_OPPORTUNITY,
            name="Confirm buyer urgency",
            status=ValidationGateStatus.NOT_STARTED,
            blocking=True,
        )
        session.add(gate)

        note = ReviewNote(
            run_id=run.id,
            target_type=ReviewTargetType.CLAIM,
            target_id=claim.id,
            author="human-reviewer",
            note="Need at least two additional sources before accepting this claim.",
        )
        session.add(note)

        decision = Decision(
            run_id=run.id,
            target_type=DecisionTargetType.RUN,
            target_id=run.id,
            decision=DecisionValue.WATCH,
            rationale="Evidence is promising but still thin.",
            decided_by="human-reviewer",
        )
        session.add(decision)

        artifact = Artifact(
            run_id=run.id,
            candidate_id=candidate.id,
            artifact_type="discovery_summary",
            title="Escalation run summary",
            path="artifacts/runs/demo/summary.md",
            created_by="agent",
        )
        session.add(artifact)

        session.commit()

    with Session(engine) as session:
        saved_run = session.scalar(select(Run).where(Run.title == "Customer support handoff bottleneck"))
        assert saved_run is not None
        assert len(saved_run.sources) == 1
        assert len(saved_run.claims) == 1
        assert len(saved_run.themes) == 1
        assert len(saved_run.candidates) == 1
        assert len(saved_run.validation_gates) == 1
        assert len(saved_run.review_notes) == 1
        assert len(saved_run.decisions) == 1
        assert len(saved_run.artifacts) == 1

        saved_claim = saved_run.claims[0]
        saved_candidate = saved_run.candidates[0]
        assert saved_claim.review_status == ReviewStatus.UNREVIEWED
        assert saved_candidate.review_status == ReviewStatus.UNREVIEWED
        assert saved_claim.is_agent_generated is True
        assert saved_candidate.is_agent_generated is True


def test_decision_history_is_durable(tmp_path) -> None:
    engine = _engine_for(tmp_path)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        run = Run(title="Decision timeline test")
        session.add(run)
        session.flush()

        session.add(
            Decision(
                run_id=run.id,
                target_type=DecisionTargetType.RUN,
                target_id=run.id,
                decision=DecisionValue.WATCH,
                decided_by="reviewer",
            )
        )
        session.add(
            Decision(
                run_id=run.id,
                target_type=DecisionTargetType.RUN,
                target_id=run.id,
                decision=DecisionValue.PROTOTYPE_LATER,
                decided_by="reviewer",
            )
        )
        session.commit()

    with Session(engine) as session:
        run = session.scalar(select(Run).where(Run.title == "Decision timeline test"))
        assert run is not None
        assert len(run.decisions) == 2
        assert [entry.decision for entry in run.decisions] == [
            DecisionValue.WATCH,
            DecisionValue.PROTOTYPE_LATER,
        ]
