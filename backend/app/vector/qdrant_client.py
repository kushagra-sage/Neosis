"""Qdrant vector-store client and bootstrap.

Two collections back the system:
  * ``noesis_papers``  — chunk embeddings of papers/patents in the Library
  * ``noesis_memory``  — embeddings of long-term research memories

``ensure_collections`` is idempotent and called on startup; it creates the
collections with the configured embedding dimension and distance metric if they
do not already exist.
"""

from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("noesis.vector")

PAPERS_COLLECTION = settings.qdrant_collection
MEMORY_COLLECTION = f"{settings.qdrant_collection}_memory"
DOCUMENTS_COLLECTION = f"{settings.qdrant_collection}_documents"

_client: AsyncQdrantClient | None = None


def get_qdrant() -> AsyncQdrantClient:
    """Return the shared async Qdrant client."""
    global _client
    if _client is None:
        api_key = settings.qdrant_api_key.get_secret_value() or None
        if settings.qdrant_prefer_grpc:
            _client = AsyncQdrantClient(
                host=settings.qdrant_host,
                grpc_port=settings.qdrant_grpc_port,
                prefer_grpc=True,
                api_key=api_key,
            )
        else:
            _client = AsyncQdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                api_key=api_key,
            )
        logger.info(
            "qdrant_client_created",
            host=settings.qdrant_host,
            grpc=settings.qdrant_prefer_grpc,
        )
    return _client


def _distance() -> qmodels.Distance:
    return qmodels.Distance[settings.vector_distance.upper()]


async def _ensure_collection(client: AsyncQdrantClient, name: str) -> None:
    exists = await client.collection_exists(name)
    if exists:
        return
    await client.create_collection(
        collection_name=name,
        vectors_config=qmodels.VectorParams(
            size=settings.embedding_dim,
            distance=_distance(),
        ),
    )
    logger.info("qdrant_collection_created", collection=name, dim=settings.embedding_dim)


async def ensure_collections() -> None:
    """Create the papers + memory collections if missing. Idempotent."""
    client = get_qdrant()
    for name in (PAPERS_COLLECTION, MEMORY_COLLECTION, DOCUMENTS_COLLECTION):
        await _ensure_collection(client, name)


async def ping_qdrant() -> bool:
    """Return True if Qdrant is reachable."""
    try:
        await get_qdrant().get_collections()
        return True
    except Exception as exc:  # pragma: no cover - exercised via health endpoint
        logger.warning("qdrant_ping_failed", error=str(exc))
        return False


async def close_qdrant() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
