"""Pydantic schemas for the system/health endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    version: str


class ReadinessResponse(BaseModel):
    ready: bool
    checks: dict[str, bool]
