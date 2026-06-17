"""Inquiry service — orchestrates pipeline execution and DB persistence."""
from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Awaitable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.enums import InquiryStatus
from app.db.models.inquiry import Inquiry
from app.pipeline.graph import run_inquiry

logger = get_logger("noesis.inquiry_svc")


async def create_and_run_inquiry(
    db: AsyncSession,
    *,
    question: str,
    user_id: str,
    workspace_id: str | None,
    token_callback: Callable[[str], Awaitable[None]] | None = None,
    stage_callback: Callable[[str, dict], Awaitable[None]] | None = None,
) -> Inquiry:
    """Run the reasoning loop, persist the result, return the Inquiry ORM object."""
    record = Inquiry(
        user_id=user_id,
        workspace_id=workspace_id,
        question=question,
        status=InquiryStatus.RUNNING,
    )
    db.add(record)
    await db.flush()

    # Activity tracking — mark the user active when they run an inquiry.
    try:
        from datetime import datetime, timezone

        from sqlalchemy import update

        from app.db.models.user import User

        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_active_at=datetime.now(timezone.utc))
        )
    except Exception:  # pragma: no cover - non-critical
        pass

    try:
        result = await run_inquiry(
            question=question,
            user_id=user_id,
            workspace_id=workspace_id,
            token_callback=token_callback,
            stage_callback=stage_callback,
        )
        record.status = (
            InquiryStatus.SUCCESS
            if not result.get("failed_operator")
            else InquiryStatus.FAILED
        )
        if not result.get("critic_passed", True):
            record.status = InquiryStatus.CRITIC_FAILED
        record.inquiry_type = result.get("inquiry_type")
        record.plan = result.get("plan")
        record.dossier = result.get("dossier")
        record.answer = result.get("answer")
        record.critic_scores = result.get("critic_scores")
        record.follow_ups = result.get("follow_ups")
        record.latency_ms = result.get("latency_ms")
    except Exception as exc:
        logger.error("inquiry_failed", error=str(exc))
        record.status = InquiryStatus.FAILED

    await db.flush()
    return record


async def get_inquiry(db: AsyncSession, inquiry_id: str, user_id: str) -> Inquiry | None:
    result = await db.execute(
        select(Inquiry).where(Inquiry.id == inquiry_id, Inquiry.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_inquiries(
    db: AsyncSession, user_id: str, workspace_id: str | None = None, limit: int = 20
) -> list[Inquiry]:
    q = select(Inquiry).where(Inquiry.user_id == user_id)
    if workspace_id:
        q = q.where(Inquiry.workspace_id == workspace_id)
    q = q.order_by(Inquiry.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())
