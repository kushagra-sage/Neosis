"""Reciprocal Rank Fusion (RRF) — merges multiple ranked lists.

Each result list is a ``list[dict]`` where each dict must have an ``id`` key
(DOI, arXiv id, or a synthetic key). The ``source`` key is used for metrics.

RRF score: sum(1 / (k + rank_i)) across all lists that contain the item.
"""
from __future__ import annotations

from typing import Any


def reciprocal_rank_fusion(
    lists: list[list[dict[str, Any]]],
    k: int = 60,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Merge *lists* via RRF and return the top *top_n* results."""
    scores: dict[str, float] = {}
    items: dict[str, dict[str, Any]] = {}

    for ranked_list in lists:
        for rank, item in enumerate(ranked_list, start=1):
            item_id = item.get("id") or item.get("title", str(rank))
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            items.setdefault(item_id, item)

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    results = []
    for item_id in sorted_ids[:top_n]:
        item = dict(items[item_id])
        item["rrf_score"] = round(scores[item_id], 6)
        results.append(item)

    return results
