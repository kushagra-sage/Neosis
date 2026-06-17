"""OpenAlex API source — 250 M+ works, completely open."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.logging import get_logger

logger = get_logger("noesis.openalex")
_BASE = "https://api.openalex.org/works"


async def search_openalex(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    params = {
        "search": query,
        "per_page": max_results,
        "select": "id,title,abstract_inverted_index,authorships,publication_year,"
                  "primary_location,cited_by_count,doi,ids",
        "mailto": "noesis@research.local",  # polite pool
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("openalex_request_failed", error=str(exc))
        return []

    results = []
    for work in data.get("results", []):
        work_id = work.get("id", "").replace("https://openalex.org/", "")
        abstract = _reconstruct_abstract(work.get("abstract_inverted_index") or {})
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in (work.get("authorships") or [])[:6]
        ]
        loc = work.get("primary_location") or {}
        url = (loc.get("landing_page_url") or work.get("doi") or "")
        doi = work.get("doi", "").replace("https://doi.org/", "")

        results.append({
            "id": f"openalex:{work_id}",
            "title": work.get("title", ""),
            "authors": authors,
            "year": work.get("publication_year"),
            "venue": (loc.get("source") or {}).get("display_name", ""),
            "abstract": abstract,
            "citation_count": work.get("cited_by_count"),
            "doi": doi,
            "url": url,
            "source": "openalex",
            "arxiv_id": work.get("ids", {}).get("arxiv", ""),
        })
    return results


def _reconstruct_abstract(inv_index: dict[str, list[int]]) -> str:
    if not inv_index:
        return ""
    positions: dict[int, str] = {}
    for word, positions_list in inv_index.items():
        for pos in positions_list:
            positions[pos] = word
    return " ".join(positions[i] for i in sorted(positions))
