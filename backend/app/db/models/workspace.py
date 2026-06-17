"""Research Workspace — the top-level container for a research thread.

A workspace owns everything related to one line of inquiry: papers, notes,
research questions, experiments, literature reviews, discovered gaps, future
ideas, a timeline of activity, and the inquiries run against it. Examples the
product ships with: "RA Severity Research", "Patent Research",
"Multimodal AI Research", "VLM Research".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import WorkspaceDomain
from app.db.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.inquiry import Inquiry
    from app.db.models.library import Note, Paper
    from app.db.models.research import (
        Experiment,
        FutureIdea,
        LiteratureReview,
        ResearchGap,
        ResearchQuestion,
    )
    from app.db.models.timeline import TimelineEvent
    from app.db.models.user import User


class Workspace(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "workspaces"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    domain: Mapped[WorkspaceDomain] = mapped_column(
        SAEnum(WorkspaceDomain, native_enum=False, length=32),
        default=WorkspaceDomain.CUSTOM,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="workspaces")

    papers: Mapped[list["Paper"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", lazy="select"
    )
    notes: Mapped[list["Note"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", lazy="select"
    )
    questions: Mapped[list["ResearchQuestion"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", lazy="select"
    )
    experiments: Mapped[list["Experiment"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", lazy="select"
    )
    reviews: Mapped[list["LiteratureReview"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", lazy="select"
    )
    gaps: Mapped[list["ResearchGap"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", lazy="select"
    )
    ideas: Mapped[list["FutureIdea"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", lazy="select"
    )
    timeline: Mapped[list["TimelineEvent"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", lazy="select"
    )
    inquiries: Mapped[list["Inquiry"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", lazy="select"
    )

    __table_args__ = (
        Index("ix_workspaces_user_id_slug", "user_id", "slug", unique=True),
        Index("ix_workspaces_user_id_updated_at", "user_id", "updated_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Workspace {self.name} ({self.domain.value})>"
