"""Pydantic schemas for workspace endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.db.models.enums import WorkspaceDomain


# ── Preset templates the frontend can offer as "quick-start" options ──────────
WORKSPACE_PRESETS: dict[str, dict[str, Any]] = {
    "ra_severity": {
        "name": "RA Severity Research",
        "domain": WorkspaceDomain.RA_SEVERITY,
        "description": (
            "Rheumatoid arthritis severity classification and prediction. "
            "Tracks papers, datasets, and experiment plans for joint-level grading models."
        ),
    },
    "patent": {
        "name": "Patent Research",
        "domain": WorkspaceDomain.PATENT,
        "description": (
            "Prior-art search and patent landscape analysis. "
            "Stores patent documents, claim comparisons, and freedom-to-operate reviews."
        ),
    },
    "multimodal_ai": {
        "name": "Multimodal AI Research",
        "domain": WorkspaceDomain.MULTIMODAL_AI,
        "description": (
            "Vision-language models, cross-modal retrieval, and multimodal benchmarks. "
            "Tracks literature, baselines, and ablation plans."
        ),
    },
    "vlm": {
        "name": "VLM Research",
        "domain": WorkspaceDomain.VLM,
        "description": (
            "Visual language model architecture, fine-tuning strategies, and evaluation. "
            "Focuses on instruction-following, grounding, and hallucination reduction."
        ),
    },
}


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    domain: WorkspaceDomain = WorkspaceDomain.CUSTOM
    description: str | None = Field(default=None, max_length=1000)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=1000)


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str
    domain: WorkspaceDomain
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceStatsResponse(BaseModel):
    papers: int
    notes: int
    questions: int
    experiments: int
    reviews: int
    gaps: int
    ideas: int
    inquiries: int


class PresetResponse(BaseModel):
    key: str
    name: str
    domain: WorkspaceDomain
    description: str
