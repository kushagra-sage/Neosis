"""Literature Review mode.

A dedicated multi-stage workflow that goes beyond a single inquiry answer:

  1. Retrieve a broad evidence base (reusing the existing hybrid retriever).
  2. Cluster the evidence into themes (LLM over the dossier).
  3. Detect consensus, disagreements, and research gaps.
  4. Synthesize a structured review with the standard academic sections.

Output is persisted as a ``LiteratureReview`` row (markdown ``content`` +
structured ``citations`` + ``critic_scores``) so it can be listed, viewed, and
exported. Reuses the existing citation infrastructure (the dossier items the
retriever already produces).
"""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.research import LiteratureReview
from app.retrieval.retriever import retrieve

logger = get_logger("noesis.litreview")

StageCb = Callable[[str, dict], Awaitable[None]]

REVIEW_TOP_K = 20


def _dossier_block(dossier: list[dict]) -> str:
    lines = []
    for i, d in enumerate(dossier, start=1):
        authors = d.get("authors") or []
        if isinstance(authors, list):
            authors = ", ".join(str(a) for a in authors[:3])
        lines.append(
            f"[{i}] {d.get('title', 'Untitled')} "
            f"({d.get('year', 'n.d.')}) — {authors or 'Unknown'}. "
            f"Source: {d.get('source', 'unknown')}.\n"
            f"    Abstract: {(d.get('abstract') or '')[:600]}"
        )
    return "\n".join(lines)


def _citations_from_dossier(dossier: list[dict]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, d in enumerate(dossier, start=1):
        out.append(
            {
                "label": f"[{i}]",
                "title": d.get("title", "Untitled"),
                "authors": d.get("authors") or [],
                "year": d.get("year"),
                "venue": d.get("venue"),
                "source": d.get("source", "unknown"),
                "url": d.get("url"),
                "doi": d.get("doi"),
                "arxiv_id": d.get("arxiv_id"),
            }
        )
    return out


_SYSTEM = """You are the Literature Review operator in Noesis, a Research Intelligence OS.
You write rigorous, well-structured literature reviews grounded ONLY in the
provided evidence. Cite every claim inline with the dossier index, e.g. [1], [2].
Never fabricate citations or facts not supported by the evidence.

Produce a complete review in Markdown with EXACTLY these sections, in order:

## Introduction
## Current State of Research
## Key Findings
## Conflicting Evidence
## Research Gaps
## Future Directions
## References

In **Key Findings**, organise the literature into 2-4 thematic clusters with
`### <Theme>` subheadings. In **Conflicting Evidence**, explicitly contrast
studies that disagree. In **Research Gaps**, state each gap on its own line
prefixed with `GAP:`. In **References**, list each cited source as
`[n] Authors (Year). Title. Venue/Source.`"""


async def _synthesize(topic: str, dossier: list[dict]) -> str:
    from app.agents._llm import get_llm
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(temperature=0.1)
    block = _dossier_block(dossier)
    human = (
        f"Topic: {topic}\n\n"
        f"Evidence dossier ({len(dossier)} sources):\n{block}\n\n"
        "Write the literature review now, following the required section structure."
    )
    resp = await llm.ainvoke(
        [SystemMessage(content=_SYSTEM), HumanMessage(content=human)]
    )
    content = resp.content
    if isinstance(content, list):  # some providers return content parts
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content).strip()


async def _self_review(topic: str, review: str, n_sources: int) -> dict[str, Any]:
    """Lightweight LLM-as-judge over the produced review."""
    from app.agents._llm import get_llm
    from langchain_core.messages import HumanMessage, SystemMessage

    judge_system = (
        "You are a strict reviewer. Score the literature review from 0.0 to 1.0 on "
        "groundedness, coverage, and rigor. Respond ONLY with compact JSON: "
        '{"groundedness": float, "coverage": float, "rigor": float, '
        '"overall": float, "pass": bool, "reasoning": "one sentence"}'
    )
    human = (
        f"Topic: {topic}\nSources available: {n_sources}\n\n"
        f"Review:\n{review[:6000]}"
    )
    try:
        llm = get_llm(temperature=0.0)
        resp = await llm.ainvoke(
            [SystemMessage(content=judge_system), HumanMessage(content=human)]
        )
        text = resp.content if isinstance(resp.content, str) else str(resp.content)
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("litreview_review_failed", error=str(exc))
    return {
        "groundedness": 0.0,
        "coverage": 0.0,
        "rigor": 0.0,
        "overall": 0.0,
        "pass": False,
        "reasoning": "Self-review unavailable.",
    }


async def generate_literature_review(
    db: AsyncSession,
    *,
    workspace_id: str,
    topic: str,
    user_id: str | None = None,
    stage_callback: StageCb | None = None,
) -> LiteratureReview:
    """Run the full literature-review workflow and persist the result."""

    async def _stage(name: str, data: dict | None = None) -> None:
        if stage_callback:
            await stage_callback(name, data or {})

    # 1) Retrieve a broad evidence base (documents + scholarly sources).
    await _stage("retrieving")
    dossier = await retrieve(
        query=topic,
        workspace_id=workspace_id,
        plan={"sources": ["arxiv", "semantic_scholar", "openalex"]},
        top_k=REVIEW_TOP_K,
        user_id=user_id,
    )
    await _stage("retrieved", {"count": len(dossier)})

    # 2-4) Cluster + synthesize the structured review.
    await _stage("synthesizing")
    if dossier:
        content = await _synthesize(topic, dossier)
    else:
        content = (
            f"## Introduction\n\nNo evidence could be retrieved for **{topic}**. "
            "Try broadening the topic or adding documents to this workspace.\n\n"
            "## Current State of Research\n\n_No sources available._\n\n"
            "## Key Findings\n\n_None._\n\n## Conflicting Evidence\n\n_None._\n\n"
            "## Research Gaps\n\nGAP: The entire area is unsupported by retrievable "
            "evidence in the current sources.\n\n## Future Directions\n\n"
            "Expand the source set or upload primary documents.\n\n## References\n\n_None._"
        )

    # 5) Self-review.
    await _stage("reviewing")
    scores = await _self_review(topic, content, len(dossier))

    # Persist.
    title = topic if len(topic) <= 120 else topic[:117] + "…"
    record = LiteratureReview(
        workspace_id=workspace_id,
        title=title,
        query=topic,
        content=content,
        citations=_citations_from_dossier(dossier),
        critic_scores=scores,
    )
    db.add(record)
    await db.flush()
    await _stage("done", {"id": record.id})
    logger.info("litreview_generated", workspace_id=workspace_id, sources=len(dossier))
    return record


async def list_reviews(
    db: AsyncSession, *, workspace_id: str
) -> list[LiteratureReview]:
    result = await db.execute(
        select(LiteratureReview)
        .where(LiteratureReview.workspace_id == workspace_id)
        .order_by(LiteratureReview.created_at.desc())
    )
    return list(result.scalars().all())


async def get_review(
    db: AsyncSession, *, review_id: str, workspace_id: str
) -> LiteratureReview | None:
    result = await db.execute(
        select(LiteratureReview).where(
            LiteratureReview.id == review_id,
            LiteratureReview.workspace_id == workspace_id,
        )
    )
    return result.scalar_one_or_none()


async def delete_review(db: AsyncSession, *, review: LiteratureReview) -> None:
    await db.delete(review)
