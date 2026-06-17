"""arXiv search source — no API key required."""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.core.logging import get_logger

logger = get_logger("noesis.arxiv")

_BASE = "https://export.arxiv.org/api/query"


async def search_arxiv(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    params = {
        "search_query": f"all:{query}",
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(_BASE, params=params)
            resp.raise_for_status()
    except Exception as exc:
        logger.warning("arxiv_request_failed", error=str(exc))
        return []

    return _parse_atom(resp.text)


def _parse_atom(xml: str) -> list[dict[str, Any]]:
    """Parse arXiv Atom feed without a heavy XML parser."""
    import xml.etree.ElementTree as ET

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    results: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []

    for entry in root.findall("atom:entry", ns):
        arxiv_id = ""
        id_el = entry.find("atom:id", ns)
        if id_el is not None and id_el.text:
            arxiv_id = id_el.text.split("/abs/")[-1]

        title = ""
        title_el = entry.find("atom:title", ns)
        if title_el is not None and title_el.text:
            title = title_el.text.strip().replace("\n", " ")

        abstract = ""
        summary_el = entry.find("atom:summary", ns)
        if summary_el is not None and summary_el.text:
            abstract = summary_el.text.strip()

        authors = [
            a.find("atom:name", ns).text
            for a in entry.findall("atom:author", ns)
            if a.find("atom:name", ns) is not None
        ]

        published = ""
        pub_el = entry.find("atom:published", ns)
        if pub_el is not None and pub_el.text:
            published = pub_el.text[:4]  # year only

        url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""

        results.append(
            {
                "id": f"arxiv:{arxiv_id}",
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "year": int(published) if published.isdigit() else None,
                "abstract": abstract,
                "url": url,
                "source": "arxiv",
                "citation_count": None,
            }
        )
    return results
