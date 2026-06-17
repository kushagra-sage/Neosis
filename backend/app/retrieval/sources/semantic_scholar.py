"""Semantic Scholar Graph API source."""
from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("noesis.s2")
_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = "paperId,title,abstract,authors,year,venue,citationCount,externalIds,openAccessPdf"


async def search_semantic_scholar(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    headers: dict[str, str] = {}
    key = settings.semantic_scholar_api_key.get_secret_value()
    if key:
        headers["x-api-key"] = key

    params = {"query": query, "limit": max_results, "fields": _FIELDS}
    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            resp = await client.get(_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("s2_request_failed", error=str(exc))
        return []

    results = []
    for paper in data.get("data", []):
        ext_ids = paper.get("externalIds") or {}
        arxiv_id = ext_ids.get("ArXiv", "")
        doi = ext_ids.get("DOI", "")
        paper_id = paper.get("paperId", "")
        url = f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else ""
        if oa := paper.get("openAccessPdf"):
            url = oa.get("url", url)

        results.append({
            "id": f"s2:{paper_id}",
            "title": paper.get("title", ""),
            "authors": [a.get("name", "") for a in (paper.get("authors") or [])],
            "year": paper.get("year"),
            "venue": paper.get("venue", ""),
            "abstract": paper.get("abstract", ""),
            "citation_count": paper.get("citationCount"),
            "arxiv_id": arxiv_id,
            "doi": doi,
            "url": url,
            "source": "semantic_scholar",
        })
    return results
