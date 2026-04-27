from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from apd.domain.models import (
    Artifact,
    Candidate,
    Claim,
    Decision,
    EvidenceExcerpt,
    EvidenceLink,
    ReviewNote,
    Run,
    Source,
    Theme,
    ValidationGate,
)


@dataclass
class RunSummary:
    run: Run
    source_count: int
    claim_count: int
    theme_count: int
    candidate_count: int


def get_recent_runs(db: Session, limit: int = 50) -> list[RunSummary]:
    stmt = (
        select(Run)
        .order_by(Run.updated_at.desc())
        .limit(limit)
    )
    runs = db.execute(stmt).scalars().all()
    result = []
    for run in runs:
        result.append(
            RunSummary(
                run=run,
                source_count=run.source_count,
                claim_count=run.claim_count,
                theme_count=run.theme_count,
                candidate_count=run.candidate_count,
            )
        )
    return result


def get_run_detail(db: Session, run_id: int) -> Optional[dict]:
    run = db.get(Run, run_id)
    if run is None:
        return None

    sources = db.execute(
        select(Source).where(Source.run_id == run_id).order_by(Source.id)
    ).scalars().all()

    claims = db.execute(
        select(Claim).where(Claim.run_id == run_id).order_by(Claim.id)
    ).scalars().all()

    themes = db.execute(
        select(Theme).where(Theme.run_id == run_id).order_by(Theme.id)
    ).scalars().all()

    candidates = db.execute(
        select(Candidate).where(Candidate.run_id == run_id).order_by(Candidate.rank.asc().nullslast(), Candidate.id)
    ).scalars().all()

    validation_gates = db.execute(
        select(ValidationGate).where(ValidationGate.run_id == run_id).order_by(ValidationGate.id)
    ).scalars().all()

    artifacts = db.execute(
        select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.id)
    ).scalars().all()

    evidence_links = db.execute(
        select(EvidenceLink).where(EvidenceLink.run_id == run_id)
    ).scalars().all()

    excerpts = {
        ex.id: ex
        for ex in db.execute(
            select(EvidenceExcerpt).where(EvidenceExcerpt.run_id == run_id)
        ).scalars().all()
    }

    review_notes = db.execute(
        select(ReviewNote).where(ReviewNote.run_id == run_id).order_by(ReviewNote.id)
    ).scalars().all()

    decision_history = db.execute(
        select(Decision).where(Decision.run_id == run_id).order_by(Decision.decided_at.desc())
    ).scalars().all()

    # Build a source lookup by id for display
    source_by_id = {s.id: s for s in sources}

    # Build evidence link index: target_type -> target_id -> list of (source_title, rel_type)
    evidence_index: dict[str, dict[int, list[dict]]] = {}
    for link in evidence_links:
        key = str(link.target_type)
        evidence_index.setdefault(key, {}).setdefault(link.target_id, [])
        src = source_by_id.get(link.source_id) if link.source_id else None
        excerpt = excerpts.get(link.excerpt_id) if link.excerpt_id else None
        evidence_index[key][link.target_id].append({
            "source_title": src.title if src else None,
            "source_id": link.source_id,
            "excerpt_id": link.excerpt_id,
            "excerpt_location": excerpt.location_reference if excerpt else None,
            "relationship_type": str(link.relationship_type),
            "strength": str(link.strength) if link.strength else None,
        })

    is_fixture = bool(
        run.metadata_json and run.metadata_json.get("is_fixture")
    )

    return {
        "run": run,
        "sources": sources,
        "claims": claims,
        "themes": themes,
        "candidates": candidates,
        "validation_gates": validation_gates,
        "artifacts": artifacts,
        "review_notes": review_notes,
        "evidence_index": evidence_index,
        "is_fixture": is_fixture,
        "decision_history": decision_history,
        "notes_by_target": _build_notes_by_target(review_notes),
    }


def _build_notes_by_target(review_notes) -> dict:
    """Build a nested dict: target_type_str -> target_id -> list of notes."""
    result: dict[str, dict[int, list]] = {}
    for n in review_notes:
        key = str(n.target_type)
        result.setdefault(key, {}).setdefault(n.target_id, []).append(n)
    return result
