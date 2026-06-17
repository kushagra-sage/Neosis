"""Celery task implementations."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.run_inquiry_async", bind=True, max_retries=1)
def run_inquiry_async(self, question: str, user_id: str, workspace_id: str | None = None) -> dict:
    """Run the reasoning pipeline asynchronously."""
    from app.pipeline.graph import run_inquiry

    async def _run() -> dict:
        return await run_inquiry(question=question, user_id=user_id, workspace_id=workspace_id)

    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="app.workers.tasks.cleanup_expired_tokens")
def cleanup_expired_tokens() -> int:
    """Delete expired refresh tokens from the database."""
    from app.db.models.auth import RefreshToken

    async def _clean() -> int:
        from sqlalchemy import delete
        from app.db.session import SessionLocal

        async with SessionLocal() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                delete(RefreshToken).where(RefreshToken.expires_at < now)
            )
            await db.commit()
            return result.rowcount

    loop = asyncio.new_event_loop()
    try:
        count = loop.run_until_complete(_clean())
    finally:
        loop.close()
    return count


@celery_app.task(name="app.workers.tasks.rebuild_bm25_index")
def rebuild_bm25_index() -> int:
    """Rebuild the in-memory BM25 index from Postgres paper metadata."""
    async def _rebuild() -> int:
        from sqlalchemy import select
        from app.db.models.library import Paper
        from app.db.session import SessionLocal
        from app.retrieval.bm25_index import load_index

        async with SessionLocal() as db:
            result = await db.execute(
                select(
                    Paper.id, Paper.workspace_id, Paper.title, Paper.abstract
                ).where(Paper.indexed.is_(True))
            )
            rows = result.all()

        docs = [
            {
                "id": str(r.id),
                "workspace_id": str(r.workspace_id),
                "title": r.title or "",
                "abstract": r.abstract or "",
            }
            for r in rows
        ]
        load_index(docs)
        return len(docs)

    loop = asyncio.new_event_loop()
    try:
        count = loop.run_until_complete(_rebuild())
    finally:
        loop.close()
    return count
