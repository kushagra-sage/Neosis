"""Admin analytics aggregations over the existing schema."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import Document
from app.db.models.inquiry import Inquiry
from app.db.models.user import User
from app.db.models.workspace import Workspace


def _since(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


async def _scalar(db: AsyncSession, stmt) -> int:  # type: ignore[no-untyped-def]
    result = await db.execute(stmt)
    return int(result.scalar_one() or 0)


async def overview(db: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    total_users = await _scalar(db, select(func.count()).select_from(User))
    new_today = await _scalar(
        db, select(func.count()).select_from(User).where(User.created_at >= _since(1))
    )
    new_week = await _scalar(
        db, select(func.count()).select_from(User).where(User.created_at >= _since(7))
    )
    new_month = await _scalar(
        db, select(func.count()).select_from(User).where(User.created_at >= _since(30))
    )
    dau = await _scalar(
        db,
        select(func.count()).select_from(User).where(User.last_active_at >= _since(1)),
    )
    wau = await _scalar(
        db,
        select(func.count()).select_from(User).where(User.last_active_at >= _since(7)),
    )
    mau = await _scalar(
        db,
        select(func.count()).select_from(User).where(User.last_active_at >= _since(30)),
    )
    total_inquiries = await _scalar(db, select(func.count()).select_from(Inquiry))
    total_workspaces = await _scalar(db, select(func.count()).select_from(Workspace))
    total_documents = await _scalar(db, select(func.count()).select_from(Document))
    storage_bytes = await _scalar(
        db, select(func.coalesce(func.sum(Document.file_size), 0))
    )

    prev_month_users = await _scalar(
        db,
        select(func.count())
        .select_from(User)
        .where(User.created_at < _since(30)),
    )
    growth_rate = (
        round((new_month / prev_month_users) * 100, 1) if prev_month_users else 0.0
    )

    return {
        "generated_at": now.isoformat(),
        "total_users": total_users,
        "new_users_today": new_today,
        "new_users_week": new_week,
        "new_users_month": new_month,
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "user_growth_rate": growth_rate,
        "total_inquiries": total_inquiries,
        "total_workspaces": total_workspaces,
        "total_documents": total_documents,
        "storage_bytes": storage_bytes,
    }


async def _daily_counts(db: AsyncSession, model, days: int) -> list[dict]:  # type: ignore[no-untyped-def]
    """Count rows per day for the last *days* days."""
    start = _since(days)
    result = await db.execute(
        select(func.date(model.created_at), func.count())
        .where(model.created_at >= start)
        .group_by(func.date(model.created_at))
        .order_by(func.date(model.created_at))
    )
    rows = result.all()
    return [{"date": str(d), "count": int(c)} for d, c in rows]


async def users_analytics(db: AsyncSession, days: int) -> dict:
    series = await _daily_counts(db, User, days)
    recent_result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(10)
    )
    recent = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "oauth_provider": u.oauth_provider,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_active_at": u.last_active_at.isoformat() if u.last_active_at else None,
        }
        for u in recent_result.scalars().all()
    ]
    return {"daily_signups": series, "recent_users": recent}


async def workspaces_analytics(db: AsyncSession, days: int) -> dict:
    series = await _daily_counts(db, Workspace, days)
    active_result = await db.execute(
        select(Workspace.id, Workspace.name, func.count(Inquiry.id).label("n"))
        .join(Inquiry, Inquiry.workspace_id == Workspace.id, isouter=True)
        .group_by(Workspace.id, Workspace.name)
        .order_by(func.count(Inquiry.id).desc())
        .limit(10)
    )
    most_active = [
        {"id": wid, "name": name, "inquiries": int(n or 0)}
        for wid, name, n in active_result.all()
    ]
    return {"daily_created": series, "most_active": most_active}


async def documents_analytics(db: AsyncSession, days: int) -> dict:
    series = await _daily_counts(db, Document, days)
    kinds_result = await db.execute(
        select(Document.kind, func.count()).group_by(Document.kind)
    )
    by_kind = [{"kind": k, "count": int(c)} for k, c in kinds_result.all()]
    storage = await _scalar(db, select(func.coalesce(func.sum(Document.file_size), 0)))
    return {"daily_uploads": series, "by_kind": by_kind, "storage_bytes": storage}


async def inquiries_analytics(db: AsyncSession, days: int) -> dict:
    series = await _daily_counts(db, Inquiry, days)
    avg_latency = await db.execute(
        select(func.coalesce(func.avg(Inquiry.latency_ms), 0))
    )
    status_result = await db.execute(
        select(Inquiry.status, func.count()).group_by(Inquiry.status)
    )
    by_status = [{"status": s, "count": int(c)} for s, c in status_result.all()]
    return {
        "daily_inquiries": series,
        "avg_latency_ms": round(float(avg_latency.scalar_one() or 0), 1),
        "by_status": by_status,
    }


async def system_analytics(db: AsyncSession) -> dict:
    from app.cache.redis_client import ping_redis
    from app.vector.qdrant_client import ping_qdrant

    redis_ok = await ping_redis()
    qdrant_ok = await ping_qdrant()
    failed = await _scalar(
        db,
        select(func.count()).select_from(Inquiry).where(Inquiry.status == "failed"),
    )
    total = await _scalar(db, select(func.count()).select_from(Inquiry))
    error_rate = round((failed / total) * 100, 2) if total else 0.0
    return {
        "redis": "ok" if redis_ok else "down",
        "qdrant": "ok" if qdrant_ok else "down",
        "inquiry_error_rate": error_rate,
        "failed_inquiries": failed,
        "total_inquiries": total,
    }
