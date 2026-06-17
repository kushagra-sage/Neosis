"""Research timeline — an append-only feed of workspace activity.

Every meaningful action (a paper analyzed, a review generated, a gap
discovered, an experiment planned) writes a TimelineEvent. The frontend renders
these as the workspace's research activity feed and progress tracker.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import TimelineEventType
from app.db.models.mixins import TimestampMixin, UUIDMixin
from app.db.types import JSONType

if TYPE_CHECKING:
    from app.db.models.workspace import Workspace


class TimelineEvent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "timeline_events"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[TimelineEventType] = mapped_column(
        SAEnum(TimelineEventType, native_enum=False, length=32), nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    # Id of the entity this event refers to (paper/review/gap/experiment/...).
    ref_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    workspace: Mapped["Workspace"] = relationship(back_populates="timeline")

    __table_args__ = (
        Index("ix_timeline_workspace_created", "workspace_id", "created_at"),
    )
