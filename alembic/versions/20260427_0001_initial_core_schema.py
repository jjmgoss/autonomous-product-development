"""create initial APD core schema

Revision ID: 20260427_0001
Revises:
Create Date: 2026-04-27 00:00:00

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260427_0001"
down_revision = None
branch_labels = None
depends_on = None


run_phase_enum = sa.Enum(
    "vague_notion",
    "evidence_collected",
    "supported_opportunity",
    "vetted_opportunity",
    "prototype_ready",
    "build_approved",
    name="runphase",
    native_enum=False,
)

review_status_enum = sa.Enum(
    "unreviewed",
    "accepted",
    "weak",
    "disputed",
    "needs_followup",
    name="reviewstatus",
    native_enum=False,
)

decision_value_enum = sa.Enum(
    "archive",
    "watch",
    "publish",
    "prototype_later",
    "build_approved",
    name="decisionvalue",
    native_enum=False,
)

evidence_relationship_enum = sa.Enum(
    "supports",
    "weakens",
    "contradicts",
    "context_for",
    "example_of",
    name="evidencerelationship",
    native_enum=False,
)

validation_gate_status_enum = sa.Enum(
    "not_started",
    "in_progress",
    "satisfied",
    "weak",
    "failed",
    "waived",
    name="validationgatestatus",
    native_enum=False,
)

evidence_target_type_enum = sa.Enum(
    "claim",
    "theme",
    "candidate",
    "validation_gate",
    name="evidencetargettype",
    native_enum=False,
)

evidence_strength_enum = sa.Enum(
    "weak",
    "medium",
    "strong",
    name="evidencestrength",
    native_enum=False,
)

review_target_type_enum = sa.Enum(
    "run",
    "source",
    "evidence_excerpt",
    "claim",
    "theme",
    "candidate",
    "validation_gate",
    "artifact",
    "decision",
    name="reviewtargettype",
    native_enum=False,
)

review_note_status_enum = sa.Enum(
    "open",
    "resolved",
    "wont_fix",
    "superseded",
    name="reviewnotestatus",
    native_enum=False,
)

decision_target_type_enum = sa.Enum(
    "run",
    "candidate",
    name="decisiontargettype",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("intent", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("mode", sa.String(length=64), nullable=True),
        sa.Column("phase", run_phase_enum, nullable=False),
        sa.Column("current_decision", decision_value_enum, nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("claim_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("theme_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("origin", sa.String(length=255), nullable=True),
        sa.Column("author_or_org", sa.String(length=255), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_path", sa.String(length=1024), nullable=True),
        sa.Column("normalized_path", sa.String(length=1024), nullable=True),
        sa.Column("reliability_notes", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_sources_run_id"), "sources", ["run_id"], unique=False)

    op.create_table(
        "evidence_excerpts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("excerpt_text", sa.Text(), nullable=False),
        sa.Column("location_reference", sa.String(length=255), nullable=True),
        sa.Column("excerpt_type", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_evidence_excerpts_run_id"), "evidence_excerpts", ["run_id"], unique=False)
    op.create_index(op.f("ix_evidence_excerpts_source_id"), "evidence_excerpts", ["source_id"], unique=False)

    op.create_table(
        "claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=64), nullable=True),
        sa.Column("review_status", review_status_enum, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("is_agent_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_claims_run_id"), "claims", ["run_id"], unique=False)

    op.create_table(
        "themes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("theme_type", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=True),
        sa.Column("frequency", sa.String(length=32), nullable=True),
        sa.Column("user_segment", sa.String(length=255), nullable=True),
        sa.Column("workflow", sa.String(length=255), nullable=True),
        sa.Column("review_status", review_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_themes_run_id"), "themes", ["run_id"], unique=False)

    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("target_user", sa.String(length=255), nullable=True),
        sa.Column("first_workflow", sa.String(length=255), nullable=True),
        sa.Column("first_wedge", sa.String(length=255), nullable=True),
        sa.Column("prototype_success_event", sa.Text(), nullable=True),
        sa.Column("monetization_path", sa.Text(), nullable=True),
        sa.Column("substitutes", sa.Text(), nullable=True),
        sa.Column("risks", sa.Text(), nullable=True),
        sa.Column("why_now", sa.Text(), nullable=True),
        sa.Column("why_it_might_fail", sa.Text(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("review_status", review_status_enum, nullable=False),
        sa.Column("decision", decision_value_enum, nullable=True),
        sa.Column("is_agent_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_candidates_run_id"), "candidates", ["run_id"], unique=False)

    op.create_table(
        "validation_gates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=True),
        sa.Column("phase", run_phase_enum, nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", validation_gate_status_enum, nullable=False),
        sa.Column("blocking", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("missing_evidence", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_validation_gates_candidate_id"), "validation_gates", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_validation_gates_run_id"), "validation_gates", ["run_id"], unique=False)

    op.create_table(
        "review_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("target_type", review_target_type_enum, nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("status", review_note_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_review_notes_run_id"), "review_notes", ["run_id"], unique=False)

    op.create_table(
        "decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=True),
        sa.Column("target_type", decision_target_type_enum, nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("decision", decision_value_enum, nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("decided_by", sa.String(length=255), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_decisions_candidate_id"), "decisions", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_decisions_run_id"), "decisions", ["run_id"], unique=False)

    op.create_table(
        "artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=True),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("path", sa.String(length=1024), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_artifacts_candidate_id"), "artifacts", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_artifacts_run_id"), "artifacts", ["run_id"], unique=False)

    op.create_table(
        "evidence_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("excerpt_id", sa.Integer(), sa.ForeignKey("evidence_excerpts.id"), nullable=True),
        sa.Column("target_type", evidence_target_type_enum, nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("relationship", evidence_relationship_enum, nullable=False),
        sa.Column("strength", evidence_strength_enum, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_evidence_links_excerpt_id"), "evidence_links", ["excerpt_id"], unique=False)
    op.create_index(op.f("ix_evidence_links_run_id"), "evidence_links", ["run_id"], unique=False)
    op.create_index(op.f("ix_evidence_links_source_id"), "evidence_links", ["source_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evidence_links_source_id"), table_name="evidence_links")
    op.drop_index(op.f("ix_evidence_links_run_id"), table_name="evidence_links")
    op.drop_index(op.f("ix_evidence_links_excerpt_id"), table_name="evidence_links")
    op.drop_table("evidence_links")

    op.drop_index(op.f("ix_artifacts_run_id"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_candidate_id"), table_name="artifacts")
    op.drop_table("artifacts")

    op.drop_index(op.f("ix_decisions_run_id"), table_name="decisions")
    op.drop_index(op.f("ix_decisions_candidate_id"), table_name="decisions")
    op.drop_table("decisions")

    op.drop_index(op.f("ix_review_notes_run_id"), table_name="review_notes")
    op.drop_table("review_notes")

    op.drop_index(op.f("ix_validation_gates_run_id"), table_name="validation_gates")
    op.drop_index(op.f("ix_validation_gates_candidate_id"), table_name="validation_gates")
    op.drop_table("validation_gates")

    op.drop_index(op.f("ix_candidates_run_id"), table_name="candidates")
    op.drop_table("candidates")

    op.drop_index(op.f("ix_themes_run_id"), table_name="themes")
    op.drop_table("themes")

    op.drop_index(op.f("ix_claims_run_id"), table_name="claims")
    op.drop_table("claims")

    op.drop_index(op.f("ix_evidence_excerpts_source_id"), table_name="evidence_excerpts")
    op.drop_index(op.f("ix_evidence_excerpts_run_id"), table_name="evidence_excerpts")
    op.drop_table("evidence_excerpts")

    op.drop_index(op.f("ix_sources_run_id"), table_name="sources")
    op.drop_table("sources")

    op.drop_table("runs")
