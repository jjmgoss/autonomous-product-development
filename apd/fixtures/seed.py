from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

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

FIXTURE_ID = "apd_demo_solo_self_hosted_v1"
FIXTURE_TITLE = "Fixture Demo: Solo builders deploying self-hosted apps"
FIXTURE_MODE = "fixture_demo"
FIXTURE_INTENT = "Synthetic fixture/demo data for APD local cockpit dogfooding."


@dataclass(frozen=True)
class SeedResult:
    created: bool
    run_id: int | None
    run_count: int
    source_count: int
    excerpt_count: int
    claim_count: int
    theme_count: int
    candidate_count: int
    evidence_link_count: int
    validation_gate_count: int
    review_note_count: int
    decision_count: int
    artifact_count: int


@dataclass(frozen=True)
class ResetResult:
    removed_runs: int


def _dt(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def _fixture_run_query():
    return select(Run).where(Run.title == FIXTURE_TITLE, Run.mode == FIXTURE_MODE)


def _count_for_run(session: Session, run_id: int) -> SeedResult:
    source_count = session.scalar(select(func.count()).select_from(Source).where(Source.run_id == run_id)) or 0
    excerpt_count = session.scalar(select(func.count()).select_from(EvidenceExcerpt).where(EvidenceExcerpt.run_id == run_id)) or 0
    claim_count = session.scalar(select(func.count()).select_from(Claim).where(Claim.run_id == run_id)) or 0
    theme_count = session.scalar(select(func.count()).select_from(Theme).where(Theme.run_id == run_id)) or 0
    candidate_count = session.scalar(select(func.count()).select_from(Candidate).where(Candidate.run_id == run_id)) or 0
    evidence_link_count = session.scalar(select(func.count()).select_from(EvidenceLink).where(EvidenceLink.run_id == run_id)) or 0
    validation_gate_count = (
        session.scalar(select(func.count()).select_from(ValidationGate).where(ValidationGate.run_id == run_id)) or 0
    )
    review_note_count = session.scalar(select(func.count()).select_from(ReviewNote).where(ReviewNote.run_id == run_id)) or 0
    decision_count = session.scalar(select(func.count()).select_from(Decision).where(Decision.run_id == run_id)) or 0
    artifact_count = session.scalar(select(func.count()).select_from(Artifact).where(Artifact.run_id == run_id)) or 0

    return SeedResult(
        created=False,
        run_id=run_id,
        run_count=1,
        source_count=source_count,
        excerpt_count=excerpt_count,
        claim_count=claim_count,
        theme_count=theme_count,
        candidate_count=candidate_count,
        evidence_link_count=evidence_link_count,
        validation_gate_count=validation_gate_count,
        review_note_count=review_note_count,
        decision_count=decision_count,
        artifact_count=artifact_count,
    )


def reset_fixture_data(session: Session) -> ResetResult:
    fixture_runs = session.scalars(_fixture_run_query()).all()
    removed = 0
    for run in fixture_runs:
        session.delete(run)
        removed += 1
    session.flush()
    return ResetResult(removed_runs=removed)


def seed_fixture_data(session: Session, *, reset_fixture: bool = False) -> SeedResult:
    if reset_fixture:
        reset_fixture_data(session)

    existing = session.scalar(_fixture_run_query().limit(1))
    if existing is not None:
        return _count_for_run(session, existing.id)

    run = Run(
        title=FIXTURE_TITLE,
        intent=FIXTURE_INTENT,
        summary=(
            "Synthetic fixture run that explores opportunities for solo builders shipping "
            "self-hosted application workflows."
        ),
        mode=FIXTURE_MODE,
        phase=RunPhase.SUPPORTED_OPPORTUNITY,
        current_decision=DecisionValue.WATCH,
        recommendation=(
            "Prioritize narrow onboarding and update-safety workflows before broader platform expansion."
        ),
        confidence=0.64,
        created_at=_dt(2026, 4, 26, 9, 0),
        updated_at=_dt(2026, 4, 26, 9, 45),
        metadata_json={
            "fixture_id": FIXTURE_ID,
            "is_fixture": True,
            "data_origin": "synthetic_demo",
        },
    )
    session.add(run)
    session.flush()

    sources = [
        Source(
            run_id=run.id,
            title="Ops forum thread: midnight rollback fatigue",
            source_type="demo_forum_thread",
            url="https://demo.local/forum/self-hosted-rollbacks",
            origin="fixture-demo",
            author_or_org="Synthetic Ops Forum",
            captured_at=_dt(2026, 4, 20, 11, 0),
            published_at=_dt(2026, 4, 19, 21, 30),
            reliability_notes="Synthetic fixture source for deterministic local tests.",
            summary="Solo maintainers report repeated downtime from manual rollback runbooks.",
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        Source(
            run_id=run.id,
            title="Indie deploy log review notes",
            source_type="demo_interview_note",
            url="https://demo.local/interviews/indie-deploy-log",
            origin="fixture-demo",
            author_or_org="Synthetic Interview Set",
            captured_at=_dt(2026, 4, 21, 15, 15),
            published_at=_dt(2026, 4, 21, 15, 0),
            reliability_notes="Synthetic fixture interview abstraction.",
            summary="Maintainers lose confidence when updates lack a safe preview and rollback checkpoint.",
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        Source(
            run_id=run.id,
            title="Community issue list: self-hosted support load",
            source_type="demo_issue_collection",
            url="https://demo.local/issues/self-hosted-support",
            origin="fixture-demo",
            author_or_org="Synthetic Community Issues",
            captured_at=_dt(2026, 4, 22, 8, 0),
            published_at=_dt(2026, 4, 22, 7, 20),
            reliability_notes="Synthetic fixture issue compilation.",
            summary="Support burden spikes when install docs drift from deploy script behavior.",
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
    ]
    session.add_all(sources)
    session.flush()

    excerpts = [
        EvidenceExcerpt(
            run_id=run.id,
            source_id=sources[0].id,
            excerpt_text="I cannot risk updates after 10pm because rollback is guesswork.",
            location_reference="post-14",
            excerpt_type="complaint",
            created_at=_dt(2026, 4, 20, 11, 5),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceExcerpt(
            run_id=run.id,
            source_id=sources[0].id,
            excerpt_text="The moment compose files diverge, recovery instructions become stale.",
            location_reference="post-22",
            excerpt_type="workaround",
            created_at=_dt(2026, 4, 20, 11, 8),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceExcerpt(
            run_id=run.id,
            source_id=sources[1].id,
            excerpt_text="Previewing diffed environment variables before deploy would avoid most incidents.",
            location_reference="note-03",
            excerpt_type="feature_request",
            created_at=_dt(2026, 4, 21, 15, 17),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceExcerpt(
            run_id=run.id,
            source_id=sources[1].id,
            excerpt_text="Most solo maintainers patch rollback scripts only after a production outage.",
            location_reference="note-07",
            excerpt_type="context",
            created_at=_dt(2026, 4, 21, 15, 19),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceExcerpt(
            run_id=run.id,
            source_id=sources[2].id,
            excerpt_text="Broken onboarding docs increase support tickets by day two of each release.",
            location_reference="issue-112",
            excerpt_type="adoption_signal",
            created_at=_dt(2026, 4, 22, 8, 3),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceExcerpt(
            run_id=run.id,
            source_id=sources[2].id,
            excerpt_text="Some teams still prefer shell scripts over control-plane tooling for transparency.",
            location_reference="issue-129",
            excerpt_type="counterevidence",
            created_at=_dt(2026, 4, 22, 8, 6),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
    ]
    session.add_all(excerpts)
    session.flush()

    claims = [
        Claim(
            run_id=run.id,
            statement="Update anxiety is driven by weak rollback confidence in solo-run environments.",
            claim_type="pain",
            review_status=ReviewStatus.UNREVIEWED,
            created_by="fixture-agent",
            is_agent_generated=True,
            confidence=0.73,
            created_at=_dt(2026, 4, 26, 9, 5),
            updated_at=_dt(2026, 4, 26, 9, 5),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        Claim(
            run_id=run.id,
            statement="Pre-deploy configuration diff previews can prevent avoidable outages.",
            claim_type="workflow",
            review_status=ReviewStatus.ACCEPTED,
            created_by="fixture-reviewer",
            is_agent_generated=False,
            confidence=0.69,
            created_at=_dt(2026, 4, 26, 9, 10),
            updated_at=_dt(2026, 4, 26, 9, 12),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        Claim(
            run_id=run.id,
            statement="Documentation drift is a recurring support burden after each release.",
            claim_type="risk",
            review_status=ReviewStatus.WEAK,
            created_by="fixture-agent",
            is_agent_generated=True,
            confidence=0.52,
            created_at=_dt(2026, 4, 26, 9, 15),
            updated_at=_dt(2026, 4, 26, 9, 16),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        Claim(
            run_id=run.id,
            statement="Operators need a narrow first workflow, not a full control-plane replacement.",
            claim_type="market_gap",
            review_status=ReviewStatus.ACCEPTED,
            created_by="fixture-reviewer",
            is_agent_generated=False,
            confidence=0.71,
            created_at=_dt(2026, 4, 26, 9, 18),
            updated_at=_dt(2026, 4, 26, 9, 20),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        Claim(
            run_id=run.id,
            statement="Some users may reject tooling that obscures plain compose workflows.",
            claim_type="counterevidence",
            review_status=ReviewStatus.DISPUTED,
            created_by="fixture-reviewer",
            is_agent_generated=False,
            confidence=0.48,
            created_at=_dt(2026, 4, 26, 9, 22),
            updated_at=_dt(2026, 4, 26, 9, 24),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
    ]
    session.add_all(claims)
    session.flush()

    themes = [
        Theme(
            run_id=run.id,
            name="Rollback confidence gap",
            summary="Solo operators need predictable rollback checkpoints before applying updates.",
            theme_type="pain_theme",
            review_status=ReviewStatus.ACCEPTED,
            created_at=_dt(2026, 4, 26, 9, 25),
            updated_at=_dt(2026, 4, 26, 9, 25),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        Theme(
            run_id=run.id,
            name="Documentation drift burden",
            summary="Install and update docs diverge from actual release steps, increasing support load.",
            theme_type="workflow_theme",
            review_status=ReviewStatus.UNREVIEWED,
            created_at=_dt(2026, 4, 26, 9, 26),
            updated_at=_dt(2026, 4, 26, 9, 26),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
    ]
    session.add_all(themes)
    session.flush()

    candidates = [
        Candidate(
            run_id=run.id,
            title="Release Guardrails Assistant",
            summary="A narrow pre-deploy checklist and rollback checkpoint generator for solo maintainers.",
            target_user="Solo maintainers of self-hosted apps",
            first_workflow="Pre-release update preparation",
            first_wedge="Rollback plan snapshot plus config diff preview",
            prototype_success_event="Maintainer completes update with no manual rollback guesswork.",
            monetization_path="Monthly subscription for advanced guardrail templates",
            risks="Could be viewed as redundant with shell script discipline",
            review_status=ReviewStatus.UNREVIEWED,
            is_agent_generated=True,
            score=0.78,
            rank=1,
            created_at=_dt(2026, 4, 26, 9, 28),
            updated_at=_dt(2026, 4, 26, 9, 28),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        Candidate(
            run_id=run.id,
            title="Self-Hosted Docs Drift Monitor",
            summary="Detect release-note and setup-doc mismatches before users hit onboarding issues.",
            target_user="Solo founders shipping frequent self-hosted releases",
            first_workflow="Release documentation validation",
            first_wedge="Checklist report highlighting docs-vs-config drift",
            prototype_success_event="Support tickets caused by stale setup docs drop after release.",
            monetization_path="Lower-cost tier tied to release frequency",
            risks="May require deeper integration than early adopters want",
            review_status=ReviewStatus.UNREVIEWED,
            is_agent_generated=True,
            score=0.66,
            rank=2,
            created_at=_dt(2026, 4, 26, 9, 30),
            updated_at=_dt(2026, 4, 26, 9, 30),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
    ]
    session.add_all(candidates)
    session.flush()

    validation_gates = [
        ValidationGate(
            run_id=run.id,
            candidate_id=candidates[0].id,
            phase=RunPhase.SUPPORTED_OPPORTUNITY,
            name="Confirm willingness to pay",
            description="Interview at least three operators who have experienced failed rollbacks.",
            status=ValidationGateStatus.NOT_STARTED,
            blocking=True,
            missing_evidence="No direct willingness-to-pay evidence in fixture set yet.",
            created_at=_dt(2026, 4, 26, 9, 33),
            updated_at=_dt(2026, 4, 26, 9, 33),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        ValidationGate(
            run_id=run.id,
            candidate_id=candidates[1].id,
            phase=RunPhase.SUPPORTED_OPPORTUNITY,
            name="Validate docs drift frequency",
            description="Collect repeated examples across at least five release cycles.",
            status=ValidationGateStatus.WEAK,
            blocking=False,
            evidence_summary="Some weak evidence exists, but breadth is low.",
            created_at=_dt(2026, 4, 26, 9, 34),
            updated_at=_dt(2026, 4, 26, 9, 34),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
    ]
    session.add_all(validation_gates)
    session.flush()

    session.add(
        ReviewNote(
            run_id=run.id,
            target_type=ReviewTargetType.CLAIM,
            target_id=claims[2].id,
            author="fixture-reviewer",
            note="Treat this as weak until cross-community corroboration exists.",
            created_at=_dt(2026, 4, 26, 9, 36),
            metadata_json={"fixture_id": FIXTURE_ID},
        )
    )

    session.add(
        Decision(
            run_id=run.id,
            target_type=DecisionTargetType.RUN,
            target_id=run.id,
            decision=DecisionValue.WATCH,
            rationale="Opportunity looks promising but requires stronger buyer and payment evidence.",
            decided_by="fixture-reviewer",
            decided_at=_dt(2026, 4, 26, 9, 40),
            metadata_json={"fixture_id": FIXTURE_ID},
        )
    )

    session.add(
        Artifact(
            run_id=run.id,
            candidate_id=candidates[0].id,
            artifact_type="discovery_summary",
            title="Fixture run summary",
            path="fixtures/demo/solo-self-hosted-summary.md",
            created_by="fixture-agent",
            created_at=_dt(2026, 4, 26, 9, 42),
            summary="Synthetic summary artifact for local app demos and screenshots.",
            metadata_json={"fixture_id": FIXTURE_ID, "synthetic": True},
        )
    )

    evidence_links = [
        EvidenceLink(
            run_id=run.id,
            source_id=sources[0].id,
            excerpt_id=excerpts[0].id,
            target_type=EvidenceTargetType.CLAIM,
            target_id=claims[0].id,
            relationship_type=EvidenceRelationship.SUPPORTS,
            notes="Rollback anxiety directly supports core pain claim.",
            created_at=_dt(2026, 4, 26, 9, 31),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceLink(
            run_id=run.id,
            source_id=sources[1].id,
            excerpt_id=excerpts[2].id,
            target_type=EvidenceTargetType.CLAIM,
            target_id=claims[1].id,
            relationship_type=EvidenceRelationship.SUPPORTS,
            created_at=_dt(2026, 4, 26, 9, 31),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceLink(
            run_id=run.id,
            source_id=sources[2].id,
            excerpt_id=excerpts[4].id,
            target_type=EvidenceTargetType.CLAIM,
            target_id=claims[2].id,
            relationship_type=EvidenceRelationship.SUPPORTS,
            created_at=_dt(2026, 4, 26, 9, 31),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceLink(
            run_id=run.id,
            source_id=sources[2].id,
            excerpt_id=excerpts[5].id,
            target_type=EvidenceTargetType.CLAIM,
            target_id=claims[4].id,
            relationship_type=EvidenceRelationship.SUPPORTS,
            created_at=_dt(2026, 4, 26, 9, 31),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceLink(
            run_id=run.id,
            source_id=sources[0].id,
            excerpt_id=excerpts[1].id,
            target_type=EvidenceTargetType.THEME,
            target_id=themes[0].id,
            relationship_type=EvidenceRelationship.EXAMPLE_OF,
            created_at=_dt(2026, 4, 26, 9, 32),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceLink(
            run_id=run.id,
            source_id=sources[2].id,
            excerpt_id=excerpts[4].id,
            target_type=EvidenceTargetType.THEME,
            target_id=themes[1].id,
            relationship_type=EvidenceRelationship.EXAMPLE_OF,
            created_at=_dt(2026, 4, 26, 9, 32),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceLink(
            run_id=run.id,
            source_id=sources[1].id,
            excerpt_id=excerpts[2].id,
            target_type=EvidenceTargetType.CANDIDATE,
            target_id=candidates[0].id,
            relationship_type=EvidenceRelationship.SUPPORTS,
            created_at=_dt(2026, 4, 26, 9, 32),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceLink(
            run_id=run.id,
            source_id=sources[2].id,
            excerpt_id=excerpts[4].id,
            target_type=EvidenceTargetType.CANDIDATE,
            target_id=candidates[1].id,
            relationship_type=EvidenceRelationship.SUPPORTS,
            created_at=_dt(2026, 4, 26, 9, 32),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
        EvidenceLink(
            run_id=run.id,
            source_id=sources[1].id,
            excerpt_id=excerpts[3].id,
            target_type=EvidenceTargetType.VALIDATION_GATE,
            target_id=validation_gates[0].id,
            relationship_type=EvidenceRelationship.CONTEXT_FOR,
            created_at=_dt(2026, 4, 26, 9, 32),
            metadata_json={"fixture_id": FIXTURE_ID},
        ),
    ]
    session.add_all(evidence_links)

    run.source_count = len(sources)
    run.claim_count = len(claims)
    run.theme_count = len(themes)
    run.candidate_count = len(candidates)
    run.updated_at = _dt(2026, 4, 26, 9, 45)

    session.flush()

    counts = _count_for_run(session, run.id)
    return SeedResult(
        created=True,
        run_id=counts.run_id,
        run_count=counts.run_count,
        source_count=counts.source_count,
        excerpt_count=counts.excerpt_count,
        claim_count=counts.claim_count,
        theme_count=counts.theme_count,
        candidate_count=counts.candidate_count,
        evidence_link_count=counts.evidence_link_count,
        validation_gate_count=counts.validation_gate_count,
        review_note_count=counts.review_note_count,
        decision_count=counts.decision_count,
        artifact_count=counts.artifact_count,
    )
