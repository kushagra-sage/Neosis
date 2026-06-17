"""System endpoints: liveness, readiness, and version.

  * ``/health``    — liveness; always 200 if the process is up.
  * ``/ready``     — readiness; pings Postgres, Redis, and Qdrant. Returns 503
                     if any dependency is unreachable (used by orchestrators).
  * ``/version``   — build/version metadata.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.cache.redis_client import ping_redis
from app.config import settings
from app.db.session import ping_db
from app.schemas.system import HealthResponse, ReadinessResponse
from app.vector.qdrant_client import ping_qdrant

router = APIRouter(tags=["system"])

__version__ = "0.1.0"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        version=__version__,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def ready(response: Response) -> ReadinessResponse:
    checks = {
        "postgres": await _safe(ping_db),
        "redis": await ping_redis(),
        "qdrant": await ping_qdrant(),
    }
    all_ready = all(checks.values())
    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(ready=all_ready, checks=checks)


@router.get("/version")
async def version() -> dict[str, str]:
    return {"service": settings.app_name, "version": __version__, "env": settings.app_env}


async def _safe(coro) -> bool:
    try:
        return bool(await coro())
    except Exception:
        return False
