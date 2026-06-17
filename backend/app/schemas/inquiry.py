"""Pydantic schemas for the inquiry endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class InquiryRequest(BaseModel):
    question: str = Field(min_length=5, max_length=2000)
    workspace_id: str | None = None
    inquiry_type: str | None = None


class DossierItem(BaseModel):
    id: str
    title: str
    authors: list[str] = []
    year: int | None = None
    venue: str | None = None
    abstract: str | None = None
    source: str
    url: str | None = None
    rrf_score: float | None = None
    citation_count: int | None = None


class CriticScores(BaseModel):
    groundedness: float
    citation_accuracy: float
    coverage: float
    rigor: float
    overall: float
    pass_: bool = Field(alias="pass", default=True)
    reasoning: str = ""
    suggestions: list[str] = []

    model_config = {"populate_by_name": True}


class InquiryResponse(BaseModel):
    id: str
    question: str
    inquiry_type: str | None
    status: str
    answer: str | None
    dossier: list[dict[str, Any]] | None
    critic_scores: dict[str, Any] | None
    follow_ups: list[str] | None
    latency_ms: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InquiryHistoryItem(BaseModel):
    id: str
    question: str
    inquiry_type: str | None
    status: str
    latency_ms: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
