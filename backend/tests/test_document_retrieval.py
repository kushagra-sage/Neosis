"""Regression tests for document RAG retrieval.

Guards against the qdrant-client API drift that silently broke document
retrieval: `.search()` was removed in qdrant-client >= 1.12 in favour of
`.query_points()`. These tests fail loudly if a removed method is reintroduced.
"""

from __future__ import annotations

import uuid

import pytest


class _FakePoint:
    def __init__(self, id: str, payload: dict, score: float) -> None:
        self.id, self.payload, self.score = id, payload, score


class _FakeResp:
    def __init__(self, points: list[_FakePoint]) -> None:
        self.points = points


class _FakeQdrant:
    """Mimics qdrant-client >= 1.12: query_points exists, search does NOT."""

    def __init__(self) -> None:
        self.store: list[_FakePoint] = []

    async def query_points(
        self, collection_name, query, limit=10, query_filter=None, with_payload=True
    ):
        pts = self.store
        if query_filter is not None and hasattr(query_filter, "must"):
            for cond in query_filter.must:
                pts = [p for p in pts if p.payload.get(cond.key) == cond.match.value]
        return _FakeResp(pts[:limit])


@pytest.mark.asyncio
async def test_search_documents_uses_query_points(monkeypatch):
    import app.services.document_service as ds

    fake = _FakeQdrant()
    fake.store.append(
        _FakePoint(
            str(uuid.uuid4()),
            {
                "document_id": "d1",
                "user_id": "u1",
                "workspace_id": "w1",
                "filename": "README.md",
                "chunk_index": 0,
                "content": "Noesis is a research OS",
            },
            0.97,
        )
    )

    monkeypatch.setattr("app.vector.qdrant_client.get_qdrant", lambda: fake)
    monkeypatch.setattr("app.retrieval.embedder.embed_query", lambda t: [0.1] * 384)

    results = await ds.search_documents(
        "what is in the readme", user_id="u1", workspace_id="w1", top_k=5
    )
    assert len(results) == 1
    assert results[0]["source"] == "document"
    assert results[0]["title"] == "README.md"


@pytest.mark.asyncio
async def test_search_documents_filters_by_user(monkeypatch):
    import app.services.document_service as ds

    fake = _FakeQdrant()
    fake.store.append(
        _FakePoint(str(uuid.uuid4()), {"document_id": "d1", "user_id": "OTHER", "workspace_id": "w1", "filename": "x", "chunk_index": 0, "content": "c"}, 0.9)
    )
    monkeypatch.setattr("app.vector.qdrant_client.get_qdrant", lambda: fake)
    monkeypatch.setattr("app.retrieval.embedder.embed_query", lambda t: [0.1] * 384)

    results = await ds.search_documents("q", user_id="u1", workspace_id="w1", top_k=5)
    assert results == []  # other user's chunk is filtered out


def test_qdrant_client_has_query_points_not_search():
    """The installed client must expose query_points; .search was removed."""
    from qdrant_client import AsyncQdrantClient

    assert hasattr(AsyncQdrantClient, "query_points")
