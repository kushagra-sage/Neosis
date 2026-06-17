"""In-memory BM25 index — rebuilt on startup / after ingest.

The index covers all papers in the Qdrant paper corpus. It is kept in memory
as a module-level singleton; the Celery beat task rebuilds it periodically.
"""
from __future__ import annotations

import asyncio
from typing import Any

from rank_bm25 import BM25Okapi

from app.core.logging import get_logger

logger = get_logger("noesis.bm25")

# (doc_id, metadata) pairs — rebuilt when load_index() is called
_index: BM25Okapi | None = None
_docs: list[dict[str, Any]] = []


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def load_index(docs: list[dict[str, Any]]) -> None:
    """Replace the in-memory BM25 index with *docs*.

    Each dict must have ``id``, ``title``, ``abstract``.
    """
    global _index, _docs
    corpus = [_tokenize(f"{d.get('title', '')} {d.get('abstract', '')}") for d in docs]
    _index = BM25Okapi(corpus) if corpus else None
    _docs = docs
    logger.info("bm25_index_loaded", n_docs=len(docs))


def bm25_search(query: str, workspace_id: str | None, top_k: int) -> list[dict[str, Any]]:
    if _index is None or not _docs:
        return []
    tokens = _tokenize(query)
    scores = _index.get_scores(tokens)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    results = []
    for idx, score in ranked[:top_k * 2]:
        doc = _docs[idx]
        if workspace_id and doc.get("workspace_id") != workspace_id:
            continue
        if score < 0.001:
            continue
        results.append({**doc, "source": "bm25", "score": float(score)})
        if len(results) == top_k:
            break
    return results
