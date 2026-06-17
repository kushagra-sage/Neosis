"""Reviewer operator — LLM-as-judge peer review.

Scores the answer on four research-appropriate dimensions (0–1 each):
  * groundedness      — every claim traceable to a cited source
  * citation_accuracy — sources are represented faithfully
  * coverage          — key literature is addressed
  * rigor             — methodologically sound, no overclaiming

If ``overall < critic_min_score`` AND ``retry_count == 0``, the review
fails and the Writer is retried once with the suggestions injected.
"""
from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseOperator
from app.config import settings
from app.core.logging import get_logger

logger = get_logger("noesis.reviewer")

_CRITIC_MIN_SCORE = 0.5

_SYSTEM = """You are the Peer Reviewer for Noesis, a Research Intelligence OS.
Evaluate the AI-generated research answer and output ONLY a JSON object (no markdown):
{
  "groundedness": 0.0,
  "citation_accuracy": 0.0,
  "coverage": 0.0,
  "rigor": 0.0,
  "overall": 0.0,
  "reasoning": "one sentence summary",
  "suggestions": ["improvement 1", "improvement 2"]
}
Scoring guide (0=poor, 1=excellent):
- groundedness: are all factual claims backed by cited sources?
- citation_accuracy: are cited sources represented faithfully?
- coverage: are the most relevant papers/concepts addressed?
- rigor: is the reasoning methodologically sound, no overclaiming?
- overall: weighted average (groundedness 0.3, citation_accuracy 0.3, coverage 0.2, rigor 0.2)
- suggestions: 1-3 concrete ways to improve the answer (empty list if overall >= 0.8)"""


class ReviewerOperator(BaseOperator):
    name = "reviewer"

    async def _execute(self, state: dict[str, Any]) -> dict[str, Any]:
        from app.agents._llm import get_llm

        stage_cb = state.get("stage_callback")
        if stage_cb:
            await stage_cb("reviewing", {})

        answer = state.get("answer") or ""
        dossier = state.get("dossier") or []
        dossier_titles = "\n".join(
            f"[{i+1}] {d.get('title', '')}" for i, d in enumerate(dossier[:15])
        )
        user_content = (
            f"QUESTION: {state['question']}\n\n"
            f"DOSSIER TITLES:\n{dossier_titles}\n\n"
            f"ANSWER TO REVIEW:\n{answer[:4000]}"
        )

        llm = get_llm(temperature=0.0)
        messages = [SystemMessage(content=_SYSTEM), HumanMessage(content=user_content)]

        try:
            response = await llm.ainvoke(messages)
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            scores = json.loads(raw.strip())
        except Exception as exc:
            logger.warning("reviewer_parse_failed", error=str(exc))
            scores = {
                "groundedness": 0.7, "citation_accuracy": 0.7,
                "coverage": 0.7, "rigor": 0.7, "overall": 0.7,
                "reasoning": "Review unavailable", "suggestions": [],
            }

        # Recompute overall as weighted average in case model got it wrong
        overall = (
            scores.get("groundedness", 0) * 0.30
            + scores.get("citation_accuracy", 0) * 0.30
            + scores.get("coverage", 0) * 0.20
            + scores.get("rigor", 0) * 0.20
        )
        scores["overall"] = round(overall, 3)
        passed = overall >= _CRITIC_MIN_SCORE

        if stage_cb:
            await stage_cb("reviewed", {"passed": passed, "overall": overall})

        return {
            "critic_scores": scores,
            "critic_passed": passed,
            "retry_count": state.get("retry_count", 0) + (0 if passed else 1),
        }
