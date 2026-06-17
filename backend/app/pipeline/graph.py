"""LangGraph reasoning loop — the Noesis pipeline.

Topology:
  planner → retriever → (conditional) → analyst → writer → reviewer
                       ↘ writer ↗

Reviewer can send the answer back to writer for one retry.

ROUTING POLICY (important):
  The retriever ALWAYS runs. Retrieval is cheap, side-effect-free, and is the
  only path that grounds an answer in the workspace's uploaded documents and the
  local corpus. A previous version gated the retriever behind the LLM planner's
  ``requires_literature`` flag; because the planner is an LLM call, that flag
  varied run-to-run for the same question, so document retrieval ran only
  sometimes — producing intermittent "there is no attached document" answers
  with an empty Evidence panel. Routing must not let a non-deterministic LLM
  decision silently bypass document grounding, so the planner→retriever edge is
  now unconditional. The planner still shapes *which* external sources are queried
  (via ``plan["sources"]``) and whether the analyst runs (``requires_computation``).
"""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.analyst import AnalystOperator
from app.agents.planner import PlannerOperator
from app.agents.retriever import RetrieverOperator
from app.agents.reviewer import ReviewerOperator
from app.agents.writer import WriterOperator
from app.core.logging import get_logger
from app.pipeline.state import InquiryState

logger = get_logger("noesis.pipeline")

# Operator singletons — shared across requests (stateless internally)
_planner = PlannerOperator()
_retriever = RetrieverOperator()
_analyst = AnalystOperator()
_writer = WriterOperator()
_reviewer = ReviewerOperator()


# ── Node wrappers ─────────────────────────────────────────────────────────────


async def planner_node(state: InquiryState) -> dict:
    return await _planner.run(state)  # type: ignore[arg-type]


async def retriever_node(state: InquiryState) -> dict:
    return await _retriever.run(state)  # type: ignore[arg-type]


async def analyst_node(state: InquiryState) -> dict:
    return await _analyst.run(state)  # type: ignore[arg-type]


async def writer_node(state: InquiryState) -> dict:
    return await _writer.run(state)  # type: ignore[arg-type]


async def reviewer_node(state: InquiryState) -> dict:
    return await _reviewer.run(state)  # type: ignore[arg-type]


# ── Conditional routing ───────────────────────────────────────────────────────


def route_after_plan(state: InquiryState) -> str:
    """Always retrieve (unless the planner hard-failed).

    Retrieval is unconditional so uploaded documents and the local corpus are
    ALWAYS searched. The planner's ``requires_literature`` flag is intentionally
    NOT consulted here — letting an LLM toggle decide whether to retrieve is what
    produced the intermittent document-grounding failures.
    """
    if state.get("failed_operator"):
        return END  # type: ignore[return-value]
    return "retriever"


def route_after_retriever(state: InquiryState) -> str:
    if state.get("failed_operator"):
        return END  # type: ignore[return-value]
    plan = state.get("plan") or {}
    if plan.get("requires_computation", False):
        return "analyst"
    return "writer"


def route_after_review(state: InquiryState) -> str:
    if state.get("critic_passed", True):
        return END  # type: ignore[return-value]
    # Allow at most 1 retry (retry_count is incremented by reviewer)
    if state.get("retry_count", 0) <= 1:
        return "writer"
    return END  # type: ignore[return-value]


# ── Compile the graph (once at module load) ───────────────────────────────────


def _build_graph() -> Any:
    g = StateGraph(InquiryState)
    g.add_node("planner", planner_node)
    g.add_node("retriever", retriever_node)
    g.add_node("analyst", analyst_node)
    g.add_node("writer", writer_node)
    g.add_node("reviewer", reviewer_node)

    g.set_entry_point("planner")
    # planner → retriever is unconditional (END only on planner failure).
    g.add_conditional_edges(
        "planner",
        route_after_plan,
        {"retriever": "retriever", END: END},
    )
    g.add_conditional_edges(
        "retriever",
        route_after_retriever,
        {"analyst": "analyst", "writer": "writer", END: END},
    )
    g.add_edge("analyst", "writer")
    g.add_edge("writer", "reviewer")
    g.add_conditional_edges(
        "reviewer",
        route_after_review,
        {"writer": "writer", END: END},
    )
    return g.compile()


_graph = _build_graph()


# ── Public entry point ────────────────────────────────────────────────────────


async def run_inquiry(
    question: str,
    user_id: str,
    workspace_id: str | None = None,
    token_callback: Callable[[str], Awaitable[None]] | None = None,
    stage_callback: Callable[[str, dict], Awaitable[None]] | None = None,
) -> dict[str, Any]:
    """Run the full reasoning loop and return the final state dict."""
    start = time.perf_counter()

    initial_state: InquiryState = {
        "question": question,
        "user_id": user_id,
        "workspace_id": workspace_id,
        "dossier": [],
        "follow_ups": [],
        "retry_count": 0,
        "failed_operator": None,
        "error_message": None,
        "token_callback": token_callback,
        "stage_callback": stage_callback,
    }

    try:
        final_state = await _graph.ainvoke(initial_state)
    except Exception as exc:
        logger.error("pipeline_failed", error=str(exc), exc_info=True)
        final_state = {**initial_state, "error_message": str(exc), "answer": None}

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "inquiry_complete",
        latency_ms=round(elapsed_ms, 1),
        passed=final_state.get("critic_passed"),
        retries=final_state.get("retry_count", 0),
    )

    # Strip non-serialisable callbacks before returning
    final_state.pop("token_callback", None)
    final_state.pop("stage_callback", None)
    final_state["latency_ms"] = round(elapsed_ms, 1)
    return dict(final_state)
