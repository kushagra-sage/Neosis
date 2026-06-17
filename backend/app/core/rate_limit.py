"""Rate limiting via Redis atomic INCR.

Implemented as an injectable dependency class so individual routes can opt in
or adjust limits, and tests can override it cleanly.

Two strategies:
  * **Per-user** (authenticated): ``noesis:rl:user:{user_id}:{window}``
  * **Per-IP guest**: ``noesis:rl:guest:{ip}:{day}``
"""

from __future__ import annotations

import time

from fastapi import HTTPException, Request, status

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("noesis.rate_limit")


class RateLimiter:
    """Callable dependency that enforces a request-count sliding window.

    Usage::

        @router.post("/inquiry")
        async def run_inquiry(
            _: Annotated[None, Depends(RateLimiter())],
            ...
        ): ...
    """

    def __init__(
        self,
        limit: int | None = None,
        window: int | None = None,
    ) -> None:
        self._limit = limit or settings.rate_limit_requests
        self._window = window or settings.rate_limit_window_seconds

    async def __call__(self, request: Request) -> None:
        from app.cache.redis_client import get_redis

        user_id: str | None = getattr(getattr(request.state, "user", None), "id", None)

        try:
            redis = get_redis()
            if user_id:
                window_key = int(time.time() // self._window)
                key = f"noesis:rl:user:{user_id}:{window_key}"
            else:
                ip = request.client.host if request.client else "unknown"
                day_key = int(time.time() // 86_400)
                key = f"noesis:rl:guest:{ip}:{day_key}"
                self._limit = min(self._limit, settings.guest_query_limit)

            count: int = await redis.incr(key)
            if count == 1:
                await redis.expire(key, self._window)

            if count > self._limit:
                retry_after = self._window - (int(time.time()) % self._window)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(retry_after)},
                )
        except HTTPException:
            raise
        except Exception as exc:
            # Redis is unavailable — fail open (allow the request) rather than
            # denying all traffic when the cache is down.
            logger.warning("rate_limit_redis_error", error=str(exc))
