"""Library models: papers/patents stored in a workspace, and free-form notes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import PaperSource
from app.db.models.mixins import TimestampMixin, UUIDMixin
from app.db.types import JSONType

if TYPE_CHECKING:
    from app.db.models.workspace import Workspace


class Paper(UUIDMixin, TimestampMixin, Base):
    """A paper or patent attached to a workspace's library."""

    __tablename__ = "papers"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list[str]] = mapped_column(JSONType, default=list)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(256), nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[PaperSource] = mapped_column(
        SAEnum(PaperSource, native_enum=False, length=32),
        default=PaperSource.UPLOAD,
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    doi: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    arxiv_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    citation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Raw uploaded file (if any) + vector index bookkeeping.
    minio_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    indexed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qdrant_point_ids: Mapped[list[str]] = mapped_column(JSONType, default=list)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    workspace: Mapped["Workspace"] = relationship(back_populates="papers")

    __table_args__ = (
        Index("ix_papers_workspace_created", "workspace_id", "created_at"),
    )


class Note(UUIDMixin, TimestampMixin, Base):
    """A free-form note, optionally anchored to a specific paper."""

    __tablename__ = "notes"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paper_id: Mapped[str | None] = mapped_column(
        ForeignKey("papers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONType, default=list)

    workspace: Mapped["Workspace"] = relationship(back_populates="notes")
