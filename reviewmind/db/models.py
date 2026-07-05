from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger, DateTime, Float, ForeignKey,
    Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── HealthCheck (Phase 1 smoke-test table) ────────────────────────────────────

class HealthCheck(Base):
    __tablename__ = "health_check"

    id: Mapped[int] = mapped_column(primary_key=True)
    note: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ── Repositories ──────────────────────────────────────────────────────────────

class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("owner", "name", name="uq_repo_owner_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    config_yaml: Mapped[str | None] = mapped_column(Text)   # cached reviewmind.yaml
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    pull_requests: Mapped[list["PullRequest"]] = relationship(back_populates="repository")


# ── Pull Requests ─────────────────────────────────────────────────────────────

class PullRequest(Base):
    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("repository_id", "pr_number", name="uq_pr_repo_number"),
        Index("ix_pr_head_sha", "head_sha"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), nullable=False)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)   # open|closed|merged
    base_branch: Mapped[str] = mapped_column(String(255))
    head_sha: Mapped[str] = mapped_column(String(40))
    additions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    repository: Mapped["Repository"] = relationship(back_populates="pull_requests")
    diff_chunks: Mapped[list["DiffChunk"]] = relationship(back_populates="pull_request")
    findings: Mapped[list["Finding"]] = relationship(back_populates="pull_request")
    reviews: Mapped[list["Review"]] = relationship(back_populates="pull_request")


# ── Diff Chunks ───────────────────────────────────────────────────────────────

class DiffChunk(Base):
    __tablename__ = "diff_chunks"
    __table_args__ = (Index("ix_chunk_pr_file", "pull_request_id", "file_path"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    pull_request_id: Mapped[int] = mapped_column(ForeignKey("pull_requests.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str] = mapped_column(String(50))   # added|modified|deleted|renamed
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    chunk_type: Mapped[str] = mapped_column(String(50))    # function|class|module|config|test
    complexity_score: Mapped[float | None] = mapped_column(Float)
    content: Mapped[str] = mapped_column(Text)

    pull_request: Mapped["PullRequest"] = relationship(back_populates="diff_chunks")
    findings: Mapped[list["Finding"]] = relationship(back_populates="diff_chunk")


# ── Findings ──────────────────────────────────────────────────────────────────

class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        Index("ix_finding_pr_category", "pull_request_id", "category"),
        Index("ix_finding_rule_id", "rule_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pull_request_id: Mapped[int] = mapped_column(ForeignKey("pull_requests.id"), nullable=False)
    diff_chunk_id: Mapped[int | None] = mapped_column(ForeignKey("diff_chunks.id"))
    category: Mapped[str] = mapped_column(String(50))      # security|style
    rule_id: Mapped[str] = mapped_column(String(20))       # SEC001, STY003, etc.
    severity: Mapped[str] = mapped_column(String(20))      # critical|high|medium|low|info
    file_path: Mapped[str] = mapped_column(Text)
    line: Mapped[int | None] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    pull_request: Mapped["PullRequest"] = relationship(back_populates="findings")
    diff_chunk: Mapped["DiffChunk | None"] = relationship(back_populates="findings")


# ── Reviews ───────────────────────────────────────────────────────────────────

class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (Index("ix_review_pr", "pull_request_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    pull_request_id: Mapped[int] = mapped_column(ForeignKey("pull_requests.id"), nullable=False)
    github_review_id: Mapped[int | None] = mapped_column(BigInteger)
    event: Mapped[str] = mapped_column(String(50))         # APPROVE|REQUEST_CHANGES|COMMENT
    body: Mapped[str] = mapped_column(Text)
    html_url: Mapped[str | None] = mapped_column(Text)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    pull_request: Mapped["PullRequest"] = relationship(back_populates="reviews")


# ── Analysis History (per-user "memory" of every analysis run) ───────────────

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    __table_args__ = (Index("ix_history_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)  # Supabase auth user id
    source: Mapped[str] = mapped_column(String(20), nullable=False)   # paste|upload|pr
    label: Mapped[str] = mapped_column(Text, nullable=False)          # filename, or "owner/repo#123"
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    security_count: Mapped[int] = mapped_column(Integer, default=0)
    style_count: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[str] = mapped_column(Text, nullable=False)        # JSON: findings + code, for reopening
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | fixed | dismissed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
