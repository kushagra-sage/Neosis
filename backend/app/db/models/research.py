"""Research artefacts produced and tracked inside a workspace.

  * ResearchQuestion  — an open question driving the inquiry
  * Experiment        — a planned study (the Experiment Planner agent fills `plan`)
  * LiteratureReview  — a generated, cited review
  * ResearchGap       — a discovered gap in the literature
  * FutureIdea        — a captured idea for later
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import (
    ExperimentStatus,
    GapStatus,
    QuestionStatus,
)
from app.db.models.mixins import TimestampMixin, UUIDMixin
from app.db.types import JSONType

if TYPE_CHECKING:
    from app.db.models.workspace import Workspace


class ResearchQuestion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "research_questions"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[QuestionStatus] = mapped_column(
        SAEnum(QuestionStatus, native_enum=False, length=24),
        default=QuestionStatus.OPEN,
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1=high

    workspace: Mapped["Workspace"] = relationship(back_populates="questions")


class Experiment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "experiments"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ExperimentStatus] = mapped_column(
        SAEnum(ExperimentStatus, native_enum=False, length=24),
        default=ExperimentStatus.PLANNED,
        nullable=False,
    )
    # Structured plan from the Experiment Planner agent:
    # {datasets, baselines, metrics, methodology, ablations, venues}
    plan: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    workspace: Mapped["Workspace"] = relationship(back_populates="experiments")


class LiteratureReview(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "literature_reviews"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)  # markdown
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    critic_scores: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    workspace: Mapped["Workspace"] = relationship(back_populates="reviews")

    __table_args__ = (
        Index("ix_reviews_workspace_created", "workspace_id", "created_at"),
    )


class ResearchGap(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "research_gaps"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[GapStatus] = mapped_column(
        SAEnum(GapStatus, native_enum=False, length=24),
        default=GapStatus.OPEN,
        nullable=False,
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="gaps")


class FutureIdea(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "future_ideas"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    workspace: Mapped["Workspace"] = relationship(back_populates="ideas")
