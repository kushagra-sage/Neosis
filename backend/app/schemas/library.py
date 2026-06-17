"""Pydantic schemas for the library (paper/note) endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.db.models.enums import PaperSource


class PaperResponse(BaseModel):
    id: str
    title: str
    authors: list[str]
    year: int | None
    venue: str | None
    abstract: str | None
    source: str
    arxiv_id: str | None
    doi: str | None
    url: str | None
    citation_count: int | None
    indexed: bool
    chunk_count: int
    created_at: datetime
    model_config = {"from_attributes": True}


class PaperImportRequest(BaseModel):
    """Import a paper from an external scholarly source (no file upload)."""
    title: str = Field(min_length=3, max_length=512)
    authors: list[str] = []
    year: int | None = None
    venue: str | None = None
    abstract: str | None = None
    source: PaperSource = PaperSource.UPLOAD
    external_id: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    url: str | None = None
    citation_count: int | None = None


class NoteCreate(BaseModel):
    title: str | None = Field(default=None, max_length=256)
    body: str = ""
    tags: list[str] = []
    paper_id: str | None = None


class NoteResponse(BaseModel):
    id: str
    workspace_id: str
    paper_id: str | None
    title: str | None
    body: str
    tags: list[str]
    created_at: datetime
    model_config = {"from_attributes": True}
