"""Long-term research memory.

Persistent, recallable memory that lets Noesis continue research across
sessions ("Last week you analyzed 15 papers on RA severity — continue?").

Each record stores a textual memory plus an optional pointer to its vector in
Qdrant's memory collection, so memories are both relationally queryable
(by user/workspace/kind) and semantically retrievable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import MemoryKind
from app.db.models.mixins import TimestampMixin, UUIDMixin
from app.db.types import JSONType

if TYPE_CHECKING:  # noqa: F401  (kept for symmetry / future relationships)
    pass


class ResearchMemory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "research_memories"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    kind: Mapped[MemoryKind] = mapped_column(
        SAEnum(MemoryKind, native_enum=False, length=32), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Pointer into the Qdrant memory collection (set once embedded).
    embedding_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Id of the source artefact (paper/review/gap/...) this memory summarises.
    source_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)
    salience: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)

    __table_args__ = (
        Index("ix_memories_user_workspace_kind", "user_id", "workspace_id", "kind"),
        Index("ix_memories_user_created", "user_id", "created_at"),
    )
