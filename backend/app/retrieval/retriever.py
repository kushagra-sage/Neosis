"""Hybrid Evidence Retriever.

Fuses ranked lists via RRF (k=60):
  1. Uploaded documents  (FastEmbed BGE → Qdrant document collection)  ← PRIORITISED
  2. Dense (FastEmbed BGE → Qdrant) — local paper corpus
  3. BM25 — same local corpus
  4. arXiv live search
  5. Semantic Scholar live search
  6. OpenAlex live search

Returns a deduplicated ``dossier``.

PRIORITY POLICY:
  When the workspace has uploaded documents that match the query, those document
  chunks are ranked ABOVE external papers (arXiv / Semantic Scholar / OpenAlex)
  and the local paper corpus. RRF alone scores a single rank-1 document the same
  as a rank-1 arXiv hit, so after fusion we apply a deterministic priority boost
  by source so document evidence reliably surfaces at the top of the dossier and
  is never truncated out by a flood of external results.
"""
from __future__ import annotations

import asyncio
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.retrieval.rrf import reciprocal_rank_fusion
from app.retrieval.sources.arxiv_source import search_arxiv
from app.retrieval.sources.openalex import search_openalex
from app.retrieval.sources.semantic_scholar import search_semantic_scholar

logger = get_logger("noesis.retriever")

# Deterministic priority by source. Higher wins. Uploaded documents and the
# workspace's own corpus outrank external scholarly APIs. Applied as a stable
# tie-break/boost on top of the RRF score so document evidence leads the dossier.
_SOURCE_PRIORITY: dict[str, int] = {
    "document": 100,      # uploaded workspace documents — highest
    "local_dense": 60,    # local paper corpus (dense)
    "local_bm25": 60,     # local paper corpus (bm25)
    "arxiv": 20,
    "semantic_scholar": 20,
    "openalex": 20,
    "patents": 10,
}
_PRIORITY_WEIGHT = 1.0  # added per priority-rank; dominates RRF ties (~0.016 each)


def _priority(source: str | None) -> int:
    return _SOURCE_PRIORITY.get(source or "", 15)


async def _dense_search(query: str, workspace_id: str | None, top_k: int) -> list[dict]:
    """Dense vector search over the Qdrant paper corpus."""
    try:
        from app.retrieval.embedder import embed_query
        from app.vector.qdrant_client import PAPERS_COLLECTION, get_qdrant

        vector = await asyncio.to_thread(embed_query, query)
        client = get_qdrant()
        response = await client.query_points(
            collection_name=PAPERS_COLLECTION,
            query=vector,
            limit=top_k,
            query_filter=(
                {"must": [{"key": "workspace_id", "match": {"value": workspace_id}}]}
                if workspace_id
                else None
            ),
            with_payload=True,
        )
        hits = response.points
        return [
            {
                "id": f"local:{h.id}",
                "title": h.payload.get("title", "") if h.payload else "",
                "abstract": h.payload.get("abstract", "") if h.payload else "",
                "authors": h.payload.get("authors", []) if h.payload else [],
                "year": h.payload.get("year") if h.payload else None,
                "source": "local_dense",
                "score": h.score,
            }
            for h in hits
        ]
    except Exception as exc:
        logger.error(
            "dense_search_failed", error_type=type(exc).__name__, error=str(exc)
        )
        return []


async def _bm25_search(query: str, workspace_id: str | None, top_k: int) -> list[dict]:
    """BM25 keyword search over the in-memory index."""
    try:
        from app.retrieval.bm25_index import bm25_search

        return await asyncio.to_thread(bm25_search, query, workspace_id, top_k)
    except Exception as exc:
        logger.warning("bm25_search_failed", error=str(exc))
        return []


async def _document_search(
    query: str, user_id: str, workspace_id: str | None, top_k: int
) -> list[dict]:
    """Dense search over the caller's uploaded documents."""
    try:
        from app.services.document_service import search_documents

        results = await search_documents(
            query, user_id=user_id, workspace_id=workspace_id, top_k=top_k
        )
        logger.info("document_source_results", count=len(results))
        return results
    except Exception as exc:
        logger.error(
            "document_source_failed",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return []


def _apply_priority(dossier: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    """Re-rank fused results so higher-priority sources lead, RRF breaks ties.

    Sort key = (source priority, rrf_score). This guarantees document evidence
    sits above external papers while preserving RRF ordering within a tier.
    """
    def _key(item: dict[str, Any]) -> tuple[float, float]:
        return (
            float(_priority(item.get("source")) * _PRIORITY_WEIGHT),
            float(item.get("rrf_score", 0.0)),
        )

    ranked = sorted(dossier, key=_key, reverse=True)
    return ranked[:top_n]


async def retrieve(
    query: str,
    workspace_id: str | None = None,
    plan: dict[str, Any] | None = None,
    top_k: int | None = None,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """Run all retrieval sources in parallel and fuse results.

    When ``user_id`` is provided, the caller's uploaded documents are searched
    and fused alongside the scholarly sources — this is the document-RAG path
    that grounds inquiries in personal/workspace knowledge. After RRF, results
    are re-ranked by source priority so uploaded documents lead the dossier.
    """
    plan = plan or {}
    top_k = top_k or settings.retriever_top_k
    # Retrieve a wider pool before priority re-ranking + truncation, so a flood
    # of external results can never push the document chunk out of the final set.
    pool_k = max(top_k * 3, 30)
    sources = set(plan.get("sources") or ["arxiv", "semantic_scholar", "openalex"])

    tasks: list[asyncio.Task] = []

    # Uploaded documents (personal + workspace knowledge base) — prioritised.
    if user_id:
        tasks.append(
            asyncio.create_task(_document_search(query, user_id, workspace_id, pool_k))
        )

    # Local corpus (always)
    tasks.append(asyncio.create_task(_dense_search(query, workspace_id, pool_k)))
    tasks.append(asyncio.create_task(_bm25_search(query, workspace_id, pool_k)))

    # Live scholarly APIs
    if "arxiv" in sources:
        tasks.append(asyncio.create_task(search_arxiv(query, top_k)))
    if "semantic_scholar" in sources:
        tasks.append(asyncio.create_task(search_semantic_scholar(query, top_k)))
    if "openalex" in sources:
        tasks.append(asyncio.create_task(search_openalex(query, top_k)))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    ranked_lists: list[list[dict]] = []
    for r in results:
        if isinstance(r, list):
            ranked_lists.append(r)
        elif isinstance(r, BaseException):
            logger.error("retrieval_source_raised", error_type=type(r).__name__, error=str(r))

    fused = reciprocal_rank_fusion(
        ranked_lists, k=settings.retriever_rrf_k, top_n=pool_k
    )
    dossier = _apply_priority(fused, top_n=top_k)

    n_docs = sum(1 for d in dossier if d.get("source") == "document")
    logger.info(
        "retrieval_done",
        sources=len(ranked_lists),
        results=len(dossier),
        documents=n_docs,
    )
    return dossier
