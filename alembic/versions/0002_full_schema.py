"""full_schema

Revision ID: 0002
Revises: 108d2ae2ccf2
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "108d2ae2ccf2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("default_branch", sa.String(255), nullable=False, server_default="main"),
        sa.Column("config_yaml", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner", "name", name="uq_repo_owner_name"),
    )

    op.create_table(
        "pull_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id"), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("state", sa.String(50), nullable=False),
        sa.Column("base_branch", sa.String(255), nullable=True),
        sa.Column("head_sha", sa.String(40), nullable=True),
        sa.Column("additions", sa.Integer(), server_default="0"),
        sa.Column("deletions", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("repository_id", "pr_number", name="uq_pr_repo_number"),
    )
    op.create_index("ix_pr_head_sha", "pull_requests", ["head_sha"])

    op.create_table(
        "diff_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pull_request_id", sa.Integer(), sa.ForeignKey("pull_requests.id"), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("change_type", sa.String(50), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("chunk_type", sa.String(50), nullable=True),
        sa.Column("complexity_score", sa.Float(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
    )
    op.create_index("ix_chunk_pr_file", "diff_chunks", ["pull_request_id", "file_path"])

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pull_request_id", sa.Integer(), sa.ForeignKey("pull_requests.id"), nullable=False),
        sa.Column("diff_chunk_id", sa.Integer(), sa.ForeignKey("diff_chunks.id"), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("rule_id", sa.String(20), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("line", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_finding_pr_category", "findings", ["pull_request_id", "category"])
    op.create_index("ix_finding_rule_id", "findings", ["rule_id"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pull_request_id", sa.Integer(), sa.ForeignKey("pull_requests.id"), nullable=False),
        sa.Column("github_review_id", sa.BigInteger(), nullable=True),
        sa.Column("event", sa.String(50), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("html_url", sa.Text(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_pr", "reviews", ["pull_request_id"])


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("findings")
    op.drop_table("diff_chunks")
    op.drop_table("pull_requests")
    op.drop_table("repositories")
