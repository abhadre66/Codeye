from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class HealthCheck(Base):
    """Smoke-test table - proves migrations + connection work end-to-end."""

    __tablename__ = "health_check"

    id: Mapped[int] = mapped_column(primary_key=True)
    note: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
