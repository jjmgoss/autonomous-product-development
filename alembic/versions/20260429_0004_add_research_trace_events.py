"""add research_trace_events table

Revision ID: 20260429_0004
Revises: 20260427_0003
Create Date: 2026-04-29 00:00:00

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260429_0004"
down_revision = "20260427_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_trace_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("brief_id", sa.Integer(), sa.ForeignKey("research_briefs.id"), nullable=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=True),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column("phase", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(op.f("ix_research_trace_events_brief_id"), "research_trace_events", ["brief_id"], unique=False)
    op.create_index(op.f("ix_research_trace_events_run_id"), "research_trace_events", ["run_id"], unique=False)
    op.create_index(
        op.f("ix_research_trace_events_correlation_id"),
        "research_trace_events",
        ["correlation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_research_trace_events_correlation_id"), table_name="research_trace_events")
    op.drop_index(op.f("ix_research_trace_events_run_id"), table_name="research_trace_events")
    op.drop_index(op.f("ix_research_trace_events_brief_id"), table_name="research_trace_events")
    op.drop_table("research_trace_events")