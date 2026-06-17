"""Async Redis client and helpers.

A single connection pool is created lazily and shared across the app. The
client is used for caching, rate limiting, pipeline checkpoints, and the
working tier of research memory. JSON (de)serialisation is handled here so
callers work with plain Python objects.
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("noesis.cache")

# TTL tiers (seconds).
TTL_SHORT = 60
TTL_MEDIUM = 60 * 15
TTL_LONG = 60 * 60
TTL_DAY = 60 * 60 * 24

_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Return the shared Redis client, creating the pool on first use."""
    global _client
    if _client is None:
        _client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        logger.info("redis_client_created", url=_redis_url_safe())
    return _client


def _redis_url_safe() -> str:
    # Avoid leaking a password into logs.
    return f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


def _key(namespace: str, key: str) -> str:
    return f"noesis:{namespace}:{key}"


async def cache_get(namespace: str, key: str) -> Any | None:
    raw = await get_redis().get(_key(namespace, key))
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


async def cache_set(namespace: str, key: str, value: Any, ttl: int = TTL_MEDIUM) -> None:
    payload = value if isinstance(value, str) else json.dumps(value, default=str)
    await get_redis().set(_key(namespace, key), payload, ex=ttl)


async def cache_delete(namespace: str, key: str) -> None:
    await get_redis().delete(_key(namespace, key))


async def ping_redis() -> bool:
    """Return True if Redis answers PING."""
    try:
        return bool(await get_redis().ping())
    except Exception as exc:  # pragma: no cover - exercised via health endpoint
        logger.warning("redis_ping_failed", error=str(exc))
        return False


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
