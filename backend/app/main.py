"""Noesis FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.cache.redis_client import close_redis, ping_redis
from app.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIDMiddleware
from app.db.session import dispose_engine, engine
from app.vector.qdrant_client import close_qdrant, ensure_collections

logger = get_logger("noesis.main")


async def _create_tables_dev() -> None:
    import app.db.models  # noqa: F401
    from app.db.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("dev_tables_created")


async def _ensure_minio() -> None:
    try:
        from minio import Minio
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key.get_secret_value(),
            secure=settings.minio_secure,
        )
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)
            logger.info("minio_bucket_created", bucket=settings.minio_bucket)
    except Exception as exc:
        logger.warning("minio_init_failed", error=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    settings.validate_runtime_secrets()
    logger.info("startup_begin", env=settings.app_env)

    # Alembic owns the schema. create_all() is only used for disposable local
    # databases when explicitly opted in via DB_AUTO_CREATE=true; otherwise run
    # `alembic upgrade head` (see scripts/entrypoint.sh).
    if settings.db_auto_create and not settings.is_production:
        logger.warning(
            "db_auto_create_enabled",
            detail="Using create_all(); this bypasses Alembic. Do not use in production.",
        )
        await _create_tables_dev()

    await ensure_collections()
    await _ensure_minio()

    if not await ping_redis():
        logger.warning("redis_unavailable_at_startup")

    logger.info("startup_complete")
    try:
        yield
    finally:
        await close_redis()
        await close_qdrant()
        await dispose_engine()
        logger.info("shutdown_complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Noesis — Research Intelligence OS",
        description="Multi-agent research copilot: plan, retrieve, analyze, synthesize, peer-review.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {"service": settings.app_name, "docs": "/docs"}

    return app


app = create_app()
