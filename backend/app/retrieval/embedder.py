"""FastEmbed ONNX embedder — BAAI/bge-small-en-v1.5 (384-dim) by default.

The model is downloaded once on first use and cached by the fastembed library.
``embed_query`` and ``embed_texts`` are synchronous; callers should use
``asyncio.to_thread`` to avoid blocking the event loop.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("noesis.embedder")


@lru_cache(maxsize=1)
def _get_model() -> Any:
    from fastembed import TextEmbedding  # type: ignore[import-untyped]
    logger.info("loading_embedding_model", model=settings.embedding_model)
    return TextEmbedding(model_name=settings.embedding_model)


def embed_query(text: str) -> list[float]:
    model = _get_model()
    vectors = list(model.embed([text]))
    return vectors[0].tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    return [v.tolist() for v in model.embed(texts)]
