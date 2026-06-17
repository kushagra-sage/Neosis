"""Inquiry — a single run of the multi-agent reasoning loop.

Records the question, the planner's classification, the assembled evidence
dossier, the synthesized answer, the reviewer's scores, and timing. This is the
auditable artefact behind every answer the system produces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import InquiryStatus, InquiryType
from app.db.models.mixins import TimestampMixin, UUIDMixin
from app.db.types import JSONType

if TYPE_CHECKING:
    from app.db.models.workspace import Workspace


class Inquiry(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "inquiries"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)

    inquiry_type: Mapped[InquiryType | None] = mapped_column(
        SAEnum(InquiryType, native_enum=False, length=32), nullable=True
    )
    output_mode: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InquiryStatus] = mapped_column(
        SAEnum(InquiryStatus, native_enum=False, length=24),
        default=InquiryStatus.PENDING,
        nullable=False,
        index=True,
    )

    plan: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    dossier: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    critic_scores: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    follow_ups: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    workspace: Mapped["Workspace | None"] = relationship(back_populates="inquiries")

    __table_args__ = (
        Index("ix_inquiries_user_created", "user_id", "created_at"),
        Index("ix_inquiries_workspace_created", "workspace_id", "created_at"),
    )
