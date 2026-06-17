"""Aggregate API v1 router."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    documents,
    export,
    health,
    inquiry,
    library,
    literature_review,
    workspaces,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(library.router)
api_router.include_router(inquiry.router)
api_router.include_router(documents.router)
api_router.include_router(admin.router)
api_router.include_router(literature_review.router)
api_router.include_router(export.router)
