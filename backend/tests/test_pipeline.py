"""Pipeline smoke tests — LLM operators are mocked; no Groq key needed."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_rrf_fusion() -> None:
    from app.retrieval.rrf import reciprocal_rank_fusion

    list_a = [{"id": "a:1", "title": "Paper One"}, {"id": "a:2", "title": "Paper Two"}]
    list_b = [{"id": "a:2", "title": "Paper Two"}, {"id": "b:3", "title": "Paper Three"}]

    merged = reciprocal_rank_fusion([list_a, list_b], k=60, top_n=3)
    assert len(merged) == 3
    # Paper Two appears in both lists, should rank highest
    assert merged[0]["id"] == "a:2"
    for item in merged:
        assert "rrf_score" in item


@pytest.mark.asyncio
async def test_circuit_breaker_trips() -> None:
    from app.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpen

    breaker = CircuitBreaker("test", failure_threshold=2, recovery_timeout=999)

    async def bad():
        raise ValueError("boom")

    for _ in range(2):
        try:
            await breaker.call(bad())
        except ValueError:
            pass

    assert breaker.state.value == "open"
    with pytest.raises(CircuitBreakerOpen):
        await breaker.call(bad())


@pytest.mark.asyncio
async def test_bulkhead_rejects_when_saturated() -> None:
    import asyncio
    from app.resilience.bulkhead import Bulkhead, BulkheadRejected

    bulkhead = Bulkhead("test", limit=1, timeout=0.05)

    async def slow():
        async with bulkhead.acquire():
            await asyncio.sleep(0.5)

    with pytest.raises(BulkheadRejected):
        await asyncio.gather(slow(), slow())


@pytest.mark.asyncio
async def test_saga_compensates_on_failure() -> None:
    from app.resilience.saga import Saga, SagaFailed

    log: list[str] = []

    async def step1():
        log.append("step1_forward")

    async def step1_comp():
        log.append("step1_compensated")

    async def step2():
        raise RuntimeError("step2 failed")

    saga = Saga("test_saga")
    saga.step(step1(), step1_comp())
    saga.step(step2(), None)

    with pytest.raises(SagaFailed):
        await saga.run()

    assert "step1_forward" in log
    assert "step1_compensated" in log


@pytest.mark.asyncio
async def test_planner_returns_valid_plan() -> None:
    from app.agents.planner import PlannerOperator

    mock_response = MagicMock()
    mock_response.content = '{"inquiry_type":"literature_review","subtasks":["What methods exist?"],"requires_literature":true,"requires_computation":false,"sources":["arxiv"],"field":"AI","time_window":"any"}'

    with patch("app.agents._llm.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm

        op = PlannerOperator()
        result = await op.run({"question": "What are the latest methods in RA severity classification?"})

    assert result["inquiry_type"] == "literature_review"
    assert result["plan"]["requires_literature"] is True
    assert "failed_operator" not in result or result.get("failed_operator") is None


@pytest.mark.asyncio
async def test_bm25_search_returns_results() -> None:
    from app.retrieval.bm25_index import bm25_search, load_index

    # BM25 IDF requires discriminating terms across docs
    docs = [
        {"id": "1", "workspace_id": "ws1", "title": "RA severity prediction rheumatoid arthritis", "abstract": "joint inflammation biomarker severity grading"},
        {"id": "2", "workspace_id": "ws1", "title": "BERT language model NLP", "abstract": "transformer attention mechanism text classification"},
        {"id": "3", "workspace_id": "ws1", "title": "image segmentation neural network", "abstract": "pixel-wise classification convolutional"},
    ]
    load_index(docs)
    results = bm25_search("rheumatoid arthritis severity", None, top_k=5)
    assert len(results) >= 1
    assert results[0]["id"] == "1"


@pytest.mark.asyncio
async def test_analyst_ast_guard() -> None:
    from app.agents.analyst import _check_ast

    good = "import math\nprint(math.pi)"
    assert _check_ast(good) is None

    bad_import = "import subprocess\nsubprocess.run(['rm', '-rf', '/'])"
    assert _check_ast(bad_import) is not None

    bad_dunder = "x.__class__.__bases__"
    assert _check_ast(bad_dunder) is not None
