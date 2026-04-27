from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apd.domain.models import (
    Candidate,
    Claim,
    EvidenceExcerpt,
    EvidenceLink,
    EvidenceRelationship,
    EvidenceStrength,
    EvidenceTargetType,
    ReviewStatus,
    Run,
    RunPhase,
    Source,
    Theme,
    ValidationGate,
    ValidationGateStatus,
)


class AgentDraftImportError(Exception):
    """Base exception for agent draft import failures."""


class AgentDraftValidationError(AgentDraftImportError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class DuplicateExternalDraftIdError(AgentDraftImportError):
    def __init__(self, external_draft_id: str, run_id: int):
        self.external_draft_id = external_draft_id
        self.run_id = run_id
        super().__init__(
            f"external_draft_id '{external_draft_id}' already imported as run {run_id}"
        )


class RunDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=1)
    intent: Optional[str] = Field(default=None, min_length=1)
    summary: Optional[str] = None
    mode: Optional[str] = Field(default=None, min_length=1, max_length=64)
    phase: Optional[RunPhase] = None
    recommendation: Optional[str] = None


class SourceDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: Optional[str] = None
    source_type: str = Field(min_length=1, max_length=64)
    url: Optional[str] = None
    origin: Optional[str] = None
    author_or_org: Optional[str] = None
    captured_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    raw_path: Optional[str] = None
    normalized_path: Optional[str] = None
    reliability_notes: Optional[str] = None
    summary: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class EvidenceExcerptDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    excerpt_text: str = Field(min_length=1)
    location_reference: Optional[str] = None
    excerpt_type: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class ClaimDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    claim_type: Optional[str] = None
    confidence: Optional[float] = None
    created_by: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class ThemeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    summary: Optional[str] = None
    theme_type: Optional[str] = None
    severity: Optional[str] = None
    frequency: Optional[str] = None
    user_segment: Optional[str] = None
    workflow: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class CandidateDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: Optional[str] = None
    target_user: Optional[str] = None
    first_workflow: Optional[str] = None
    first_wedge: Optional[str] = None
    prototype_success_event: Optional[str] = None
    monetization_path: Optional[str] = None
    substitutes: Optional[str] = None
    risks: Optional[str] = None
    why_now: Optional[str] = None
    why_it_might_fail: Optional[str] = None
    score: Optional[float] = None
    rank: Optional[int] = None
    metadata_json: Optional[dict[str, Any]] = None


class ValidationGateDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    candidate_id: Optional[str] = None
    phase: Optional[RunPhase] = None
    name: str = Field(min_length=1)
    description: Optional[str] = None
    status: Optional[ValidationGateStatus] = None
    blocking: bool = True
    evidence_summary: Optional[str] = None
    missing_evidence: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class EvidenceLinkDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    source_id: Optional[str] = None
    excerpt_id: Optional[str] = None
    target_type: EvidenceTargetType
    target_id: str = Field(min_length=1)
    relationship: EvidenceRelationship
    strength: Optional[EvidenceStrength] = None
    notes: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class AgentDraftPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0", min_length=1)
    external_draft_id: Optional[str] = Field(default=None, min_length=1)
    agent_name: Optional[str] = None
    generated_at: Optional[datetime] = None
    run: RunDraft
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    sources: list[SourceDraft] = Field(default_factory=list)
    evidence_excerpts: list[EvidenceExcerptDraft] = Field(default_factory=list)
    claims: list[ClaimDraft] = Field(default_factory=list)
    themes: list[ThemeDraft] = Field(default_factory=list)
    candidates: list[CandidateDraft] = Field(default_factory=list)
    validation_gates: list[ValidationGateDraft] = Field(default_factory=list)
    evidence_links: list[EvidenceLinkDraft] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_minimum_content(self) -> "AgentDraftPackage":
        if not (self.run.title or self.run.intent):
            raise ValueError("run.title or run.intent is required")

        if not (self.sources or self.claims or self.candidates):
            raise ValueError("at least one source or one claim or one candidate is required")

        _validate_unique_ids("sources", self.sources)
        _validate_unique_ids("evidence_excerpts", self.evidence_excerpts)
        _validate_unique_ids("claims", self.claims)
        _validate_unique_ids("themes", self.themes)
        _validate_unique_ids("candidates", self.candidates)
        _validate_unique_ids("validation_gates", self.validation_gates)
        _validate_unique_ids("evidence_links", self.evidence_links)
        return self


@dataclass
class AgentDraftImportResult:
    run_db_id: int
    external_draft_id: Optional[str]
    created_run: bool
    imported_source_count: int
    imported_excerpt_count: int
    imported_claim_count: int
    imported_theme_count: int
    imported_candidate_count: int
    imported_validation_gate_count: int
    imported_evidence_link_count: int
    warnings: list[str]


def load_agent_draft_package(path: Path) -> AgentDraftPackage:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentDraftValidationError([f"could not read draft package: {exc}"]) from exc

    try:
        raw_data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise AgentDraftValidationError([f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"]) from exc

    try:
        return AgentDraftPackage.model_validate(raw_data)
    except ValidationError as exc:
        errors: list[str] = []
        for err in exc.errors():
            location = ".".join(str(part) for part in err.get("loc", []))
            message = err.get("msg", "validation error")
            errors.append(f"{location}: {message}" if location else message)
        raise AgentDraftValidationError(errors) from exc


def import_agent_draft_file(
    db: Session,
    path: Path,
    *,
    allow_duplicate_external_id: bool = False,
) -> AgentDraftImportResult:
    package = load_agent_draft_package(path)
    return import_agent_draft_package(
        db,
        package,
        package_path=path,
        allow_duplicate_external_id=allow_duplicate_external_id,
    )


def import_agent_draft_package(
    db: Session,
    package: AgentDraftPackage,
    *,
    package_path: Optional[Path] = None,
    allow_duplicate_external_id: bool = False,
) -> AgentDraftImportResult:
    if package.external_draft_id and not allow_duplicate_external_id:
        existing = _find_existing_external_draft_run(db, package.external_draft_id)
        if existing is not None:
            raise DuplicateExternalDraftIdError(package.external_draft_id, existing.id)

    warnings = list(package.warnings)

    run = Run(
        title=package.run.title or _title_from_intent_or_external(package.run.intent, package.external_draft_id),
        intent=package.run.intent,
        summary=package.run.summary,
        mode=package.run.mode or "agent_draft_import",
        phase=package.run.phase or _default_phase(package),
        recommendation=package.run.recommendation,
        metadata_json={
            "agent_draft": {
                "schema_version": package.schema_version,
                "external_draft_id": package.external_draft_id,
                "agent_name": package.agent_name,
                "generated_at": package.generated_at.isoformat() if package.generated_at else None,
                "limitations": package.limitations,
                "imported_at": datetime.now(timezone.utc).isoformat(),
                "package_path": _repo_relative_or_abs(package_path),
            }
        },
    )
    db.add(run)
    db.flush()

    source_ids: dict[str, int] = {}
    excerpt_ids: dict[str, int] = {}
    claim_ids: dict[str, int] = {}
    theme_ids: dict[str, int] = {}
    candidate_ids: dict[str, int] = {}
    validation_gate_ids: dict[str, int] = {}

    for source in package.sources:
        source_row = Source(
            run_id=run.id,
            title=source.title,
            source_type=source.source_type,
            url=source.url,
            origin=source.origin or "agent_draft_import",
            author_or_org=source.author_or_org,
            captured_at=source.captured_at,
            published_at=source.published_at,
            raw_path=source.raw_path,
            normalized_path=source.normalized_path,
            reliability_notes=source.reliability_notes,
            summary=source.summary,
            metadata_json={
                **(source.metadata_json or {}),
                "agent_draft_id": source.id,
                "agent_generated": True,
            },
        )
        db.add(source_row)
        db.flush()
        source_ids[source.id] = source_row.id

    for excerpt in package.evidence_excerpts:
        source_id = source_ids.get(excerpt.source_id)
        if source_id is None:
            warnings.append(
                f"skipped excerpt '{excerpt.id}': unknown source_id '{excerpt.source_id}'"
            )
            continue

        excerpt_row = EvidenceExcerpt(
            run_id=run.id,
            source_id=source_id,
            excerpt_text=excerpt.excerpt_text,
            location_reference=excerpt.location_reference,
            excerpt_type=excerpt.excerpt_type,
            metadata_json={
                **(excerpt.metadata_json or {}),
                "agent_draft_id": excerpt.id,
                "agent_generated": True,
            },
        )
        db.add(excerpt_row)
        db.flush()
        excerpt_ids[excerpt.id] = excerpt_row.id

    for claim in package.claims:
        claim_row = Claim(
            run_id=run.id,
            statement=claim.statement,
            claim_type=claim.claim_type,
            review_status=ReviewStatus.UNREVIEWED,
            confidence=claim.confidence,
            created_by=claim.created_by or package.agent_name or "agent_draft_import",
            is_agent_generated=True,
            metadata_json={
                **(claim.metadata_json or {}),
                "agent_draft_id": claim.id,
                "agent_generated": True,
            },
        )
        db.add(claim_row)
        db.flush()
        claim_ids[claim.id] = claim_row.id

    for theme in package.themes:
        theme_row = Theme(
            run_id=run.id,
            name=theme.name,
            summary=theme.summary,
            theme_type=theme.theme_type,
            severity=theme.severity,
            frequency=theme.frequency,
            user_segment=theme.user_segment,
            workflow=theme.workflow,
            review_status=ReviewStatus.UNREVIEWED,
            metadata_json={
                **(theme.metadata_json or {}),
                "agent_draft_id": theme.id,
                "agent_generated": True,
            },
        )
        db.add(theme_row)
        db.flush()
        theme_ids[theme.id] = theme_row.id

    for candidate in package.candidates:
        candidate_row = Candidate(
            run_id=run.id,
            title=candidate.title,
            summary=candidate.summary,
            target_user=candidate.target_user,
            first_workflow=candidate.first_workflow,
            first_wedge=candidate.first_wedge,
            prototype_success_event=candidate.prototype_success_event,
            monetization_path=candidate.monetization_path,
            substitutes=candidate.substitutes,
            risks=candidate.risks,
            why_now=candidate.why_now,
            why_it_might_fail=candidate.why_it_might_fail,
            score=candidate.score,
            rank=candidate.rank,
            review_status=ReviewStatus.UNREVIEWED,
            is_agent_generated=True,
            metadata_json={
                **(candidate.metadata_json or {}),
                "agent_draft_id": candidate.id,
                "agent_generated": True,
            },
        )
        db.add(candidate_row)
        db.flush()
        candidate_ids[candidate.id] = candidate_row.id

    for gate in package.validation_gates:
        candidate_id = None
        if gate.candidate_id:
            candidate_id = candidate_ids.get(gate.candidate_id)
            if candidate_id is None:
                warnings.append(
                    f"validation_gate '{gate.id}' references unknown candidate_id '{gate.candidate_id}'; candidate link omitted"
                )

        gate_row = ValidationGate(
            run_id=run.id,
            candidate_id=candidate_id,
            phase=gate.phase,
            name=gate.name,
            description=gate.description,
            status=gate.status or ValidationGateStatus.NOT_STARTED,
            blocking=gate.blocking,
            evidence_summary=gate.evidence_summary,
            missing_evidence=gate.missing_evidence,
            metadata_json={
                **(gate.metadata_json or {}),
                "agent_draft_id": gate.id,
                "agent_generated": True,
            },
        )
        db.add(gate_row)
        db.flush()
        validation_gate_ids[gate.id] = gate_row.id

    for link in package.evidence_links:
        target_id = _map_target_id(
            link.target_type,
            link.target_id,
            claim_ids,
            theme_ids,
            candidate_ids,
            validation_gate_ids,
        )
        if target_id is None:
            warnings.append(
                f"skipped evidence_link '{link.id}': unknown {link.target_type.value} target_id '{link.target_id}'"
            )
            continue

        source_id = None
        if link.source_id is not None:
            source_id = source_ids.get(link.source_id)
            if source_id is None:
                warnings.append(
                    f"skipped evidence_link '{link.id}': unknown source_id '{link.source_id}'"
                )
                continue

        excerpt_id = None
        if link.excerpt_id is not None:
            excerpt_id = excerpt_ids.get(link.excerpt_id)
            if excerpt_id is None:
                warnings.append(
                    f"skipped evidence_link '{link.id}': unknown excerpt_id '{link.excerpt_id}'"
                )
                continue

        link_row = EvidenceLink(
            run_id=run.id,
            source_id=source_id,
            excerpt_id=excerpt_id,
            target_type=link.target_type,
            target_id=target_id,
            relationship_type=link.relationship,
            strength=link.strength,
            notes=link.notes,
            metadata_json={
                **(link.metadata_json or {}),
                "agent_draft_id": link.id,
                "agent_generated": True,
                "source_external_id": link.source_id,
                "excerpt_external_id": link.excerpt_id,
                "target_external_id": link.target_id,
            },
        )
        db.add(link_row)

    db.flush()

    run.source_count = _count_rows_for_run(db, Source, run.id)
    run.claim_count = _count_rows_for_run(db, Claim, run.id)
    run.theme_count = _count_rows_for_run(db, Theme, run.id)
    run.candidate_count = _count_rows_for_run(db, Candidate, run.id)
    run.updated_at = datetime.now(timezone.utc)
    run.metadata_json = {
        **(run.metadata_json or {}),
        "agent_draft": {
            **((run.metadata_json or {}).get("agent_draft") or {}),
            "import_warnings": warnings,
        },
    }

    db.commit()
    db.refresh(run)

    return AgentDraftImportResult(
        run_db_id=run.id,
        external_draft_id=package.external_draft_id,
        created_run=True,
        imported_source_count=run.source_count,
        imported_excerpt_count=_count_rows_for_run(db, EvidenceExcerpt, run.id),
        imported_claim_count=run.claim_count,
        imported_theme_count=run.theme_count,
        imported_candidate_count=run.candidate_count,
        imported_validation_gate_count=_count_rows_for_run(db, ValidationGate, run.id),
        imported_evidence_link_count=_count_rows_for_run(db, EvidenceLink, run.id),
        warnings=warnings,
    )


def _validate_unique_ids(name: str, items: list[Any]) -> None:
    seen: set[str] = set()
    for item in items:
        item_id = item.id
        if item_id in seen:
            raise ValueError(f"duplicate {name} id: {item_id}")
        seen.add(item_id)


def _find_existing_external_draft_run(db: Session, external_draft_id: str) -> Optional[Run]:
    runs = db.execute(select(Run)).scalars().all()
    for run in runs:
        metadata = run.metadata_json or {}
        draft_meta = metadata.get("agent_draft") if isinstance(metadata, dict) else None
        if isinstance(draft_meta, dict) and draft_meta.get("external_draft_id") == external_draft_id:
            return run
    return None


def _title_from_intent_or_external(intent: Optional[str], external_draft_id: Optional[str]) -> str:
    if intent:
        return intent[:255]
    if external_draft_id:
        return f"Agent Draft {external_draft_id}"[:255]
    return "Imported Agent Draft"


def _default_phase(package: AgentDraftPackage) -> RunPhase:
    if package.sources:
        return RunPhase.EVIDENCE_COLLECTED
    return RunPhase.VAGUE_NOTION


def _map_target_id(
    target_type: EvidenceTargetType,
    external_target_id: str,
    claim_ids: dict[str, int],
    theme_ids: dict[str, int],
    candidate_ids: dict[str, int],
    validation_gate_ids: dict[str, int],
) -> Optional[int]:
    if target_type == EvidenceTargetType.CLAIM:
        return claim_ids.get(external_target_id)
    if target_type == EvidenceTargetType.THEME:
        return theme_ids.get(external_target_id)
    if target_type == EvidenceTargetType.CANDIDATE:
        return candidate_ids.get(external_target_id)
    if target_type == EvidenceTargetType.VALIDATION_GATE:
        return validation_gate_ids.get(external_target_id)
    return None


def _count_rows_for_run(db: Session, model: Any, run_id: int) -> int:
    return db.scalar(select(func.count()).select_from(model).where(model.run_id == run_id)) or 0


def _repo_relative_or_abs(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    repo_root = Path(__file__).resolve().parents[2]
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()
