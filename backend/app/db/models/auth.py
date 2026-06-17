"""RefreshToken model — JWT refresh-token rotation.

Each issued refresh token is stored as a SHA-256 hash of its JTI (JWT ID
claim). On every ``/auth/refresh`` call the old token is atomically revoked
and a new one is issued. This prevents replay attacks: a stolen refresh token
can only be used once before it is replaced, and using a revoked token
immediately signals a compromise.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDMixin


class RefreshToken(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # SHA-256 hex digest of the token's ``jti`` claim.
    token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    # First 120 chars of the User-Agent — helps users identify sessions.
    device_hint: Mapped[str | None] = mapped_column(String(120), nullable=True)

    __table_args__ = (
        Index("ix_refresh_tokens_user_revoked", "user_id", "revoked"),
    )
