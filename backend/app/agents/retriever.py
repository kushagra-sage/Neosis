"""Evidence Retriever operator — LangGraph node."""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseOperator
from app.retrieval.retriever import retrieve


class RetrieverOperator(BaseOperator):
    name = "retriever"

    async def _execute(self, state: dict[str, Any]) -> dict[str, Any]:
        stage_cb = state.get("stage_callback")
        if stage_cb:
            await stage_cb("retrieving", {})

        dossier = await retrieve(
            query=state["question"],
            workspace_id=state.get("workspace_id"),
            plan=state.get("plan"),
            top_k=10,
            user_id=state.get("user_id"),
        )
        if stage_cb:
            await stage_cb("retrieved", {"count": len(dossier)})

        return {"dossier": dossier}
