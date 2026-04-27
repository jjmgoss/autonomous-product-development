"""add research_briefs table

Revision ID: 20260427_0002
Revises: 20260427_0001
Create Date: 2026-04-27 00:00:00

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260427_0002"
down_revision = "20260427_0001"
branch_labels = None
depends_on = None

research_brief_status_enum = sa.Enum(
    "draft",
    "ready",
    "external_agent_prompted",
    "imported",
    "archived",
    name="researchbriefstatus",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "research_briefs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("research_question", sa.Text(), nullable=False),
        sa.Column("constraints", sa.Text(), nullable=True),
        sa.Column("desired_depth", sa.String(64), nullable=True),
        sa.Column("expected_outputs", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            research_brief_status_enum,
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("research_briefs")
