from __future__ import annotations

from datetime import datetime
from datetime import timezone
from enum import StrEnum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apd.app.db import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunPhase(StrEnum):
    VAGUE_NOTION = "vague_notion"
    EVIDENCE_COLLECTED = "evidence_collected"
    SUPPORTED_OPPORTUNITY = "supported_opportunity"
    VETTED_OPPORTUNITY = "vetted_opportunity"
    PROTOTYPE_READY = "prototype_ready"
    BUILD_APPROVED = "build_approved"


class ReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    ACCEPTED = "accepted"
    WEAK = "weak"
    DISPUTED = "disputed"
    NEEDS_FOLLOWUP = "needs_followup"


class DecisionValue(StrEnum):
    ARCHIVE = "archive"
    WATCH = "watch"
    PUBLISH = "publish"
    PROTOTYPE_LATER = "prototype_later"
    BUILD_APPROVED = "build_approved"


class EvidenceRelationship(StrEnum):
    SUPPORTS = "supports"
    WEAKENS = "weakens"
    CONTRADICTS = "contradicts"
    CONTEXT_FOR = "context_for"
    EXAMPLE_OF = "example_of"


class ValidationGateStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SATISFIED = "satisfied"
    WEAK = "weak"
    FAILED = "failed"
    WAIVED = "waived"


class EvidenceTargetType(StrEnum):
    CLAIM = "claim"
    THEME = "theme"
    CANDIDATE = "candidate"
    VALIDATION_GATE = "validation_gate"


class ReviewTargetType(StrEnum):
    RUN = "run"
    SOURCE = "source"
    EVIDENCE_EXCERPT = "evidence_excerpt"
    CLAIM = "claim"
    THEME = "theme"
    CANDIDATE = "candidate"
    VALIDATION_GATE = "validation_gate"
    ARTIFACT = "artifact"
    DECISION = "decision"


class DecisionTargetType(StrEnum):
    RUN = "run"
    CANDIDATE = "candidate"


class ReviewNoteStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"
    SUPERSEDED = "superseded"


class EvidenceStrength(StrEnum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


class ResearchBriefStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    EXTERNAL_AGENT_PROMPTED = "external_agent_prompted"
    IMPORTED = "imported"
    ARCHIVED = "archived"


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    mode: Mapped[Optional[str]] = mapped_column(String(64))
    phase: Mapped[RunPhase] = mapped_column(
        SqlEnum(RunPhase, native_enum=False, validate_strings=True),
        nullable=False,
        default=RunPhase.VAGUE_NOTION,
    )
    current_decision: Mapped[Optional[DecisionValue]] = mapped_column(
        SqlEnum(DecisionValue, native_enum=False, validate_strings=True),
        nullable=True,
    )
    recommendation: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    claim_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    theme_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    sources: Mapped[list[Source]] = relationship(back_populates="run", cascade="all, delete-orphan")
    evidence_excerpts: Mapped[list[EvidenceExcerpt]] = relationship(back_populates="run", cascade="all, delete-orphan")
    claims: Mapped[list[Claim]] = relationship(back_populates="run", cascade="all, delete-orphan")
    themes: Mapped[list[Theme]] = relationship(back_populates="run", cascade="all, delete-orphan")
    candidates: Mapped[list[Candidate]] = relationship(back_populates="run", cascade="all, delete-orphan")
    evidence_links: Mapped[list[EvidenceLink]] = relationship(back_populates="run", cascade="all, delete-orphan")
    validation_gates: Mapped[list[ValidationGate]] = relationship(back_populates="run", cascade="all, delete-orphan")
    review_notes: Mapped[list[ReviewNote]] = relationship(back_populates="run", cascade="all, delete-orphan")
    decisions: Mapped[list[Decision]] = relationship(back_populates="run", cascade="all, delete-orphan")
    artifacts: Mapped[list[Artifact]] = relationship(back_populates="run", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1024))
    origin: Mapped[Optional[str]] = mapped_column(String(255))
    author_or_org: Mapped[Optional[str]] = mapped_column(String(255))
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    raw_path: Mapped[Optional[str]] = mapped_column(String(1024))
    normalized_path: Mapped[Optional[str]] = mapped_column(String(1024))
    reliability_notes: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    run: Mapped[Run] = relationship(back_populates="sources")
    evidence_excerpts: Mapped[list[EvidenceExcerpt]] = relationship(back_populates="source", cascade="all, delete-orphan")
    evidence_links: Mapped[list[EvidenceLink]] = relationship(back_populates="source")


class EvidenceExcerpt(Base):
    __tablename__ = "evidence_excerpts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False, index=True)
    excerpt_text: Mapped[str] = mapped_column(Text, nullable=False)
    location_reference: Mapped[Optional[str]] = mapped_column(String(255))
    excerpt_type: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    run: Mapped[Run] = relationship(back_populates="evidence_excerpts")
    source: Mapped[Source] = relationship(back_populates="evidence_excerpts")
    evidence_links: Mapped[list[EvidenceLink]] = relationship(back_populates="excerpt")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[Optional[str]] = mapped_column(String(64))
    review_status: Mapped[ReviewStatus] = mapped_column(
        SqlEnum(ReviewStatus, native_enum=False, validate_strings=True),
        nullable=False,
        default=ReviewStatus.UNREVIEWED,
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    is_agent_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    run: Mapped[Run] = relationship(back_populates="claims")


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    theme_type: Mapped[Optional[str]] = mapped_column(String(64))
    severity: Mapped[Optional[str]] = mapped_column(String(32))
    frequency: Mapped[Optional[str]] = mapped_column(String(32))
    user_segment: Mapped[Optional[str]] = mapped_column(String(255))
    workflow: Mapped[Optional[str]] = mapped_column(String(255))
    review_status: Mapped[ReviewStatus] = mapped_column(
        SqlEnum(ReviewStatus, native_enum=False, validate_strings=True),
        nullable=False,
        default=ReviewStatus.UNREVIEWED,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    run: Mapped[Run] = relationship(back_populates="themes")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    target_user: Mapped[Optional[str]] = mapped_column(String(255))
    first_workflow: Mapped[Optional[str]] = mapped_column(String(255))
    first_wedge: Mapped[Optional[str]] = mapped_column(String(255))
    prototype_success_event: Mapped[Optional[str]] = mapped_column(Text)
    monetization_path: Mapped[Optional[str]] = mapped_column(Text)
    substitutes: Mapped[Optional[str]] = mapped_column(Text)
    risks: Mapped[Optional[str]] = mapped_column(Text)
    why_now: Mapped[Optional[str]] = mapped_column(Text)
    why_it_might_fail: Mapped[Optional[str]] = mapped_column(Text)
    score: Mapped[Optional[float]] = mapped_column(Float)
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    review_status: Mapped[ReviewStatus] = mapped_column(
        SqlEnum(ReviewStatus, native_enum=False, validate_strings=True),
        nullable=False,
        default=ReviewStatus.UNREVIEWED,
    )
    decision: Mapped[Optional[DecisionValue]] = mapped_column(
        SqlEnum(DecisionValue, native_enum=False, validate_strings=True),
        nullable=True,
    )
    is_agent_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    run: Mapped[Run] = relationship(back_populates="candidates")
    validation_gates: Mapped[list[ValidationGate]] = relationship(back_populates="candidate")
    decisions: Mapped[list[Decision]] = relationship(back_populates="candidate")
    artifacts: Mapped[list[Artifact]] = relationship(back_populates="candidate")


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    source_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sources.id"), index=True)
    excerpt_id: Mapped[Optional[int]] = mapped_column(ForeignKey("evidence_excerpts.id"), index=True)
    target_type: Mapped[EvidenceTargetType] = mapped_column(
        SqlEnum(EvidenceTargetType, native_enum=False, validate_strings=True),
        nullable=False,
    )
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    relationship_type: Mapped[EvidenceRelationship] = mapped_column(
        "relationship",
        SqlEnum(EvidenceRelationship, native_enum=False, validate_strings=True),
        nullable=False,
    )
    strength: Mapped[Optional[EvidenceStrength]] = mapped_column(
        SqlEnum(EvidenceStrength, native_enum=False, validate_strings=True),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    run: Mapped[Run] = relationship(back_populates="evidence_links")
    source: Mapped[Optional[Source]] = relationship(back_populates="evidence_links")
    excerpt: Mapped[Optional[EvidenceExcerpt]] = relationship(back_populates="evidence_links")


class ValidationGate(Base):
    __tablename__ = "validation_gates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"), index=True)
    phase: Mapped[Optional[RunPhase]] = mapped_column(
        SqlEnum(RunPhase, native_enum=False, validate_strings=True),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ValidationGateStatus] = mapped_column(
        SqlEnum(ValidationGateStatus, native_enum=False, validate_strings=True),
        nullable=False,
        default=ValidationGateStatus.NOT_STARTED,
    )
    blocking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    evidence_summary: Mapped[Optional[str]] = mapped_column(Text)
    missing_evidence: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    run: Mapped[Run] = relationship(back_populates="validation_gates")
    candidate: Mapped[Optional[Candidate]] = relationship(back_populates="validation_gates")


class ReviewNote(Base):
    __tablename__ = "review_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    target_type: Mapped[ReviewTargetType] = mapped_column(
        SqlEnum(ReviewTargetType, native_enum=False, validate_strings=True),
        nullable=False,
    )
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(255))
    note: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReviewNoteStatus] = mapped_column(
        SqlEnum(ReviewNoteStatus, native_enum=False, validate_strings=True),
        nullable=False,
        default=ReviewNoteStatus.OPEN,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    run: Mapped[Run] = relationship(back_populates="review_notes")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"), index=True)
    target_type: Mapped[DecisionTargetType] = mapped_column(
        SqlEnum(DecisionTargetType, native_enum=False, validate_strings=True),
        nullable=False,
    )
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[DecisionValue] = mapped_column(
        SqlEnum(DecisionValue, native_enum=False, validate_strings=True),
        nullable=False,
    )
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    decided_by: Mapped[Optional[str]] = mapped_column(String(255))
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    run: Mapped[Run] = relationship(back_populates="decisions")
    candidate: Mapped[Optional[Candidate]] = relationship(back_populates="decisions")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"), index=True)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    path: Mapped[Optional[str]] = mapped_column(String(1024))
    url: Mapped[Optional[str]] = mapped_column(String(1024))
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)

    run: Mapped[Run] = relationship(back_populates="artifacts")
    candidate: Mapped[Optional[Candidate]] = relationship(back_populates="artifacts")


class ResearchBrief(Base):
    __tablename__ = "research_briefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    research_question: Mapped[str] = mapped_column(Text, nullable=False)
    constraints: Mapped[Optional[str]] = mapped_column(Text)
    desired_depth: Mapped[Optional[str]] = mapped_column(String(64))
    expected_outputs: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ResearchBriefStatus] = mapped_column(
        SqlEnum(ResearchBriefStatus, native_enum=False, validate_strings=True),
        nullable=False,
        default=ResearchBriefStatus.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)
