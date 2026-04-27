from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from apd.domain.models import (
    Candidate,
    Claim,
    Decision,
    DecisionTargetType,
    DecisionValue,
    ReviewNote,
    ReviewNoteStatus,
    ReviewStatus,
    ReviewTargetType,
    Run,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def update_claim_review_status(
    db: Session,
    run_id: int,
    claim_id: int,
    new_status: ReviewStatus,
    note_text: Optional[str] = None,
    author: Optional[str] = None,
) -> Optional[Claim]:
    claim = db.get(Claim, claim_id)
    if claim is None or claim.run_id != run_id:
        return None
    claim.review_status = new_status
    claim.updated_at = _utc_now()
    if note_text and note_text.strip():
        note = ReviewNote(
            run_id=run_id,
            target_type=ReviewTargetType.CLAIM,
            target_id=claim_id,
            note=note_text.strip(),
            author=author,
            status=ReviewNoteStatus.OPEN,
        )
        db.add(note)
    db.commit()
    db.refresh(claim)
    return claim


def update_candidate_review_status(
    db: Session,
    run_id: int,
    candidate_id: int,
    new_status: ReviewStatus,
    note_text: Optional[str] = None,
    author: Optional[str] = None,
) -> Optional[Candidate]:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None or candidate.run_id != run_id:
        return None
    candidate.review_status = new_status
    candidate.updated_at = _utc_now()
    if note_text and note_text.strip():
        note = ReviewNote(
            run_id=run_id,
            target_type=ReviewTargetType.CANDIDATE,
            target_id=candidate_id,
            note=note_text.strip(),
            author=author,
            status=ReviewNoteStatus.OPEN,
        )
        db.add(note)
    db.commit()
    db.refresh(candidate)
    return candidate


def add_review_note(
    db: Session,
    run_id: int,
    target_type: ReviewTargetType,
    target_id: int,
    note_text: str,
    author: Optional[str] = None,
) -> Optional[ReviewNote]:
    # Verify the run exists
    run = db.get(Run, run_id)
    if run is None:
        return None
    note = ReviewNote(
        run_id=run_id,
        target_type=target_type,
        target_id=target_id,
        note=note_text.strip(),
        author=author,
        status=ReviewNoteStatus.OPEN,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_run_decision(
    db: Session,
    run_id: int,
    new_decision: DecisionValue,
    rationale: Optional[str] = None,
    decided_by: Optional[str] = None,
) -> Optional[Run]:
    run = db.get(Run, run_id)
    if run is None:
        return None
    run.current_decision = new_decision
    run.updated_at = _utc_now()
    # Preserve history in the Decision table
    decision_record = Decision(
        run_id=run_id,
        candidate_id=None,
        target_type=DecisionTargetType.RUN,
        target_id=run_id,
        decision=new_decision,
        rationale=rationale.strip() if rationale and rationale.strip() else None,
        decided_by=decided_by,
        decided_at=_utc_now(),
    )
    db.add(decision_record)
    db.commit()
    db.refresh(run)
    return run
