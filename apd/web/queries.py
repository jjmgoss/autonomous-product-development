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

    # Build lookups for inference
    claims_by_id = {c.id: c for c in claims}
    themes_by_id = {t.id: t for t in themes}

    # Map validation gates by candidate for quick access
    gates_by_candidate: dict[int, list[ValidationGate]] = {}
    for g in validation_gates:
        if g.candidate_id:
            gates_by_candidate.setdefault(g.candidate_id, []).append(g)

    # Build candidate-centered relations by inferring shared evidence (source/excerpt)
    candidate_relations: dict[int, dict] = {}
    # Precompute evidence references per target for faster checks
    def _refs_for_links(links: list[dict]) -> tuple[set[int], set[int]]:
        sids = set()
        eids = set()
        for L in links:
            if L.get("source_id"):
                sids.add(L.get("source_id"))
            if L.get("excerpt_id"):
                eids.add(L.get("excerpt_id"))
        return sids, eids

    candidate_links_index = evidence_index.get("candidate", {})
    claim_links_index = evidence_index.get("claim", {})
    theme_links_index = evidence_index.get("theme", {})

    for c in candidates:
        clinks = candidate_links_index.get(c.id, [])
        c_sids, c_eids = _refs_for_links(clinks)

        # Find claims/themes that share source or excerpt references with the candidate
        related_claims: list[Claim] = []
        for cid, clinks in claim_links_index.items():
            sids, eids = _refs_for_links(clinks)
            if (sids & c_sids) or (eids & c_eids):
                claim_obj = claims_by_id.get(cid)
                if claim_obj:
                    related_claims.append(claim_obj)

        related_themes: list[Theme] = []
        for tid, tlinks in theme_links_index.items():
            sids, eids = _refs_for_links(tlinks)
            if (sids & c_sids) or (eids & c_eids):
                theme_obj = themes_by_id.get(tid)
                if theme_obj:
                    related_themes.append(theme_obj)

        candidate_relations[c.id] = {
            "evidence": clinks,
            "gates": gates_by_candidate.get(c.id, []),
            "related_claims": related_claims,
            "related_themes": related_themes,
        }

    # Unlinked material (not inferred to belong to any candidate)
    linked_claim_ids = {cl.id for rel in candidate_relations.values() for cl in rel["related_claims"]}
    linked_theme_ids = {t.id for rel in candidate_relations.values() for t in rel["related_themes"]}
    linked_gate_ids = {g.id for rel in candidate_relations.values() for g in rel["gates"]}

    unlinked_claims = [c for c in claims if c.id not in linked_claim_ids]
    unlinked_themes = [t for t in themes if t.id not in linked_theme_ids]
    unlinked_validation_gates = [g for g in validation_gates if g.id not in linked_gate_ids]

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
        "candidate_relations": candidate_relations,
        "unlinked_claims": unlinked_claims,
        "unlinked_themes": unlinked_themes,
        "unlinked_validation_gates": unlinked_validation_gates,
    }


def _build_notes_by_target(review_notes) -> dict:
    """Build a nested dict: target_type_str -> target_id -> list of notes."""
    result: dict[str, dict[int, list]] = {}
    for n in review_notes:
        key = str(n.target_type)
        result.setdefault(key, {}).setdefault(n.target_id, []).append(n)
    return result
