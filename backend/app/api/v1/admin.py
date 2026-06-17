"""Admin analytics endpoints (admin-only).

  GET /admin/analytics/overview
  GET /admin/analytics/users
  GET /admin/analytics/workspaces
  GET /admin/analytics/documents
  GET /admin/analytics/inquiries
  GET /admin/analytics/system
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.security.dependencies import AdminUser
from app.services import analytics_service

router = APIRouter(prefix="/admin", tags=["admin"])

RangeDays = Literal[1, 7, 30, 90, 365]
_RANGE_MAP = {"24h": 1, "7d": 7, "30d": 30, "90d": 90, "all": 365}


def _days(range_: str) -> int:
    return _RANGE_MAP.get(range_, 30)


@router.get("/analytics/overview")
async def analytics_overview(
    _: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await analytics_service.overview(db)


@router.get("/analytics/users")
async def analytics_users(
    _: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    range: str = Query(default="30d"),
) -> dict:
    return await analytics_service.users_analytics(db, _days(range))


@router.get("/analytics/workspaces")
async def analytics_workspaces(
    _: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    range: str = Query(default="30d"),
) -> dict:
    return await analytics_service.workspaces_analytics(db, _days(range))


@router.get("/analytics/documents")
async def analytics_documents(
    _: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    range: str = Query(default="30d"),
) -> dict:
    return await analytics_service.documents_analytics(db, _days(range))


@router.get("/analytics/inquiries")
async def analytics_inquiries(
    _: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    range: str = Query(default="30d"),
) -> dict:
    return await analytics_service.inquiries_analytics(db, _days(range))


@router.get("/analytics/system")
async def analytics_system(
    _: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await analytics_service.system_analytics(db)
