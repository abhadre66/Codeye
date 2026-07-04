"""analysis_history

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-04
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("findings_count", sa.Integer(), server_default="0"),
        sa.Column("security_count", sa.Integer(), server_default="0"),
        sa.Column("style_count", sa.Integer(), server_default="0"),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_history_user_created", "analysis_history", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_history_user_created", table_name="analysis_history")
    op.drop_table("analysis_history")
