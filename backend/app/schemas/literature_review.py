"""Schemas for Literature Review mode."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LiteratureReviewRequest(BaseModel):
    topic: str = Field(min_length=5, max_length=2000)


class LiteratureReviewResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    query: str
    content: str
    citations: list[dict[str, Any]]
    critic_scores: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class LiteratureReviewListItem(BaseModel):
    id: str
    title: str
    query: str
    created_at: datetime

    model_config = {"from_attributes": True}
