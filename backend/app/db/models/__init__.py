"""ORM model registry — import this package to populate Base.metadata."""

from __future__ import annotations

from app.db.base import Base
from app.db.models.auth import RefreshToken
from app.db.models.document import Document, DocumentChunk
from app.db.models.password_reset import PasswordResetToken
from app.db.models.inquiry import Inquiry
from app.db.models.library import Note, Paper
from app.db.models.memory import ResearchMemory
from app.db.models.research import (
    Experiment,
    FutureIdea,
    LiteratureReview,
    ResearchGap,
    ResearchQuestion,
)
from app.db.models.timeline import TimelineEvent
from app.db.models.user import User
from app.db.models.workspace import Workspace

__all__ = [
    "Base",
    "RefreshToken",
    "PasswordResetToken",
    "Document",
    "DocumentChunk",
    "User",
    "Workspace",
    "Paper",
    "Note",
    "ResearchQuestion",
    "Experiment",
    "LiteratureReview",
    "ResearchGap",
    "FutureIdea",
    "TimelineEvent",
    "ResearchMemory",
    "Inquiry",
]
