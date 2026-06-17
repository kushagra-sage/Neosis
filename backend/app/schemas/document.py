"""Schemas for the document upload + knowledge-base endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    file_size: int
    kind: str
    status: str
    chunk_count: int
    workspace_id: str | None
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    id: str
    filename: str
    kind: str
    status: str
    file_size: int
    chunk_count: int
    workspace_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
