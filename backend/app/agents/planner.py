"""Inquiry Planner — decomposes the research question into a structured plan.

Calls the LLM (T=0) and returns a typed plan that drives routing:
  - ``inquiry_type``         which kind of research task this is
  - ``requires_literature``  should the Retriever run?
  - ``requires_computation`` should the Analyst run?
  - ``sources``              which scholarly APIs to query
  - ``field``                detected research domain
"""
from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseOperator
from app.core.logging import get_logger

logger = get_logger("noesis.planner")

_SYSTEM = """You are the Inquiry Planner for Noesis, a research intelligence OS.
Given a research question, output ONLY a JSON object (no markdown fences) with:
{
  "inquiry_type": "literature_review|gap_analysis|prior_art|experiment_design|methodology|factual",
  "subtasks": ["sub-question 1", "sub-question 2"],
  "requires_literature": true,
  "requires_computation": false,
  "sources": ["arxiv","semantic_scholar","openalex"],
  "field": "detected field, e.g. biomedical AI, NLP, materials science",
  "time_window": "any|recent_3_years|recent_5_years"
}
Rules:
- subtasks: 1-4 focused sub-questions
- requires_literature: true unless the question is purely factual/definitional
- requires_computation: true only if the user explicitly asks for calculations, statistics, or code
- sources: include "patents" only for prior-art questions
- For experiment_design questions, set requires_computation true"""

_FALLBACK_PLAN = {
    "inquiry_type": "literature_review",
    "subtasks": [],
    "requires_literature": True,
    "requires_computation": False,
    "sources": ["arxiv", "semantic_scholar", "openalex"],
    "field": "general",
    "time_window": "any",
}


class PlannerOperator(BaseOperator):
    name = "planner"

    async def _execute(self, state: dict[str, Any]) -> dict[str, Any]:
        from app.agents._llm import get_llm
        from app.pipeline.state import InquiryState

        stage_cb = state.get("stage_callback")
        if stage_cb:
            await stage_cb("planning", {})

        question = state["question"]
        llm = get_llm(temperature=0.0)
        messages = [SystemMessage(content=_SYSTEM), HumanMessage(content=question)]

        try:
            response = await llm.ainvoke(messages)
            raw = response.content.strip()
            # Strip markdown fences if the model added them anyway
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            plan = json.loads(raw.strip())
        except Exception as exc:
            logger.warning("planner_parse_failed", error=str(exc))
            plan = {**_FALLBACK_PLAN}

        plan.setdefault("requires_literature", True)
        plan.setdefault("requires_computation", False)
        plan["subtasks"] = plan.get("subtasks", [])[:4]

        return {
            "plan": plan,
            "inquiry_type": plan.get("inquiry_type", "literature_review"),
            "output_mode": plan.get("inquiry_type", "literature_review"),
        }
