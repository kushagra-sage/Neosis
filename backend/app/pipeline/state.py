"""InquiryState — the single mutable object threaded through the LangGraph."""
from __future__ import annotations

from collections.abc import Callable, Awaitable
from typing import Any, TypedDict


class InquiryState(TypedDict, total=False):
    # ── Input ─────────────────────────────────────────────────────────────────
    question: str
    user_id: str
    workspace_id: str | None

    # ── Planner output ────────────────────────────────────────────────────────
    inquiry_type: str            # literature_review | gap_analysis | prior_art |
                                  # experiment_design | methodology | factual
    output_mode: str
    plan: dict[str, Any]         # {subtasks, requires_literature, requires_computation,
                                  #  sources, field, time_window}

    # ── Retriever output ─────────────────────────────────────────────────────
    dossier: list[dict[str, Any]]  # ranked evidence items

    # ── Analyst output ────────────────────────────────────────────────────────
    code_output: str
    code_error: str

    # ── Writer output ─────────────────────────────────────────────────────────
    answer: str
    follow_ups: list[str]

    # ── Reviewer output ───────────────────────────────────────────────────────
    critic_scores: dict[str, Any]
    critic_passed: bool
    retry_count: int

    # ── Error handling ────────────────────────────────────────────────────────
    failed_operator: str | None
    error_message: str | None

    # ── Streaming callbacks (injected by the API layer, not persisted) ────────
    token_callback: Callable[[str], Awaitable[None]] | None
    stage_callback: Callable[[str, dict], Awaitable[None]] | None
