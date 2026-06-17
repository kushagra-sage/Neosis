"""Writer operator — synthesizes a grounded, cited research answer.

Streams tokens through ``state['token_callback']``. Adjusts the prompt based
on ``output_mode`` (literature_review / gap_analysis / experiment_design / …).
Always appends 3 follow-up research directions.

DOCUMENT GROUNDING:
  Uploaded documents (source == "document") are labelled [D1], [D2], … and are
  presented FIRST in the dossier with their full chunk text (not truncated),
  because the chunk content IS the evidence. The system prompt instructs the
  writer to rely on uploaded documents over external papers when both are
  present, so a question like "what is in my uploaded document?" is answered
  from the document verbatim.
"""
from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseOperator
from app.core.logging import get_logger

logger = get_logger("noesis.writer")

# Per-source citation label prefix. Documents get D; scholarly sources keep their
# existing letters. The number always matches the dossier position.
_SOURCE_PREFIX = {
    "document": "D",
    "local_dense": "L",
    "local_bm25": "L",
    "arxiv": "A",
    "semantic_scholar": "S",
    "openalex": "O",
    "patents": "P",
}

# Document chunks are the primary evidence — keep far more of their text than a
# paper abstract (chunks are ~1200 chars; abstracts are summarised).
_DOC_CHUNK_CHARS = 1500
_ABSTRACT_CHARS = 300

_MODE_INSTRUCTIONS = {
    "literature_review": (
        "Structure your answer as a mini literature review with sections: "
        "**Background**, **Key Findings**, **Methods Compared**, **Open Questions**. "
        "Cite inline using the dossier labels, e.g. [D1] (uploaded document), "
        "[S1] (Semantic Scholar), [A2] (arXiv), [P3] (Patent). "
    ),
    "gap_analysis": (
        "Clearly identify what is well-studied and what is under-researched. "
        "State each gap explicitly as 'GAP: …'. "
        "Cite inline using the dossier labels, e.g. [D1], [S1], [A2]. "
    ),
    "experiment_design": (
        "Produce: 1) Hypothesis, 2) Recommended Datasets, 3) Baselines, "
        "4) Evaluation Metrics, 5) Methodology, 6) Sample Size / Power Analysis, "
        "7) Publication Venue suggestions. "
        "Cite inline using the dossier labels, e.g. [D1], [S1], [A2]. "
    ),
    "prior_art": (
        "Analyze the retrieved patents/papers claim by claim. "
        "State clearly which aspects of the user's concept are anticipated. "
        "Cite inline using the dossier labels, e.g. [D1], [P1], [S2]. "
    ),
    "factual": (
        "Answer concisely and precisely. Cite every claim with its dossier label, "
        "e.g. [D1], [S1], [A2]. If an uploaded document [D#] answers the question, "
        "quote the relevant fact from it directly. "
    ),
    "methodology": (
        "Describe the research methodology step-by-step. "
        "Cite relevant sources using the dossier labels, e.g. [D1], [S1], [A2]. "
    ),
}

_SYSTEM_BASE = """You are the Writer operator in Noesis, a Research Intelligence OS.
You produce grounded, peer-review-ready research answers.

IMPORTANT:
- The EVIDENCE DOSSIER below is your only source of truth. Cite EVERY factual
  claim with the inline label shown in the dossier (e.g. [D1], [S2], [A3]) where
  the number matches the dossier position.
- Items labelled [D#] are documents the user uploaded to this workspace. When the
  question is about the user's uploaded document(s), or when a [D#] item is
  relevant, ANSWER FROM THOSE DOCUMENTS DIRECTLY and quote the relevant content.
  Prefer uploaded documents [D#] over external papers when both are relevant.
- If the dossier contains the answer, do NOT say there is no document or no
  evidence — use it.
- Never fabricate citations or facts not present in the dossier.
- At the end, add a section "**Further Research Directions:**" with exactly 3
  numbered follow-up questions.
- Use academic prose. Be precise and thorough.
{mode_instruction}"""


def _build_dossier_block(dossier: list[dict]) -> str:
    if not dossier:
        return "No external sources retrieved."
    lines = ["EVIDENCE DOSSIER:"]
    for i, doc in enumerate(dossier[:15], start=1):
        source = doc.get("source", "S")
        prefix = _SOURCE_PREFIX.get(source, source[0].upper() if source else "S")
        label = f"[{prefix}{i}]"
        authors = ", ".join((doc.get("authors") or [])[:3])
        year = f" ({doc['year']})" if doc.get("year") else ""
        # Uploaded documents: include the full chunk text (it IS the evidence).
        limit = _DOC_CHUNK_CHARS if source == "document" else _ABSTRACT_CHARS
        body = (doc.get("abstract") or "")[:limit]
        title = doc.get("title", "Untitled")
        kind = " [UPLOADED DOCUMENT]" if source == "document" else ""
        lines.append(
            f"{label} {title}{year}{kind} — {authors}\n    {body}"
        )
    return "\n".join(lines)


class WriterOperator(BaseOperator):
    name = "writer"

    async def _execute(self, state: dict[str, Any]) -> dict[str, Any]:
        from app.agents._llm import get_llm

        stage_cb = state.get("stage_callback")
        token_cb = state.get("token_callback")
        if stage_cb:
            await stage_cb("writing", {})

        mode = state.get("output_mode") or state.get("inquiry_type") or "literature_review"
        mode_instruction = _MODE_INSTRUCTIONS.get(mode, _MODE_INSTRUCTIONS["literature_review"])
        system_prompt = _SYSTEM_BASE.format(mode_instruction=mode_instruction)

        dossier = state.get("dossier") or []
        dossier_block = _build_dossier_block(dossier)
        code_context = ""
        if state.get("code_output"):
            code_context = f"\n\nCOMPUTATIONAL ANALYSIS OUTPUT:\n{state['code_output']}"

        retry_note = ""
        if state.get("retry_count", 0) > 0:
            prev_suggestions = (state.get("critic_scores") or {}).get("suggestions", [])
            if prev_suggestions:
                retry_note = (
                    "\n\nPEER REVIEW FEEDBACK — address these in your revision:\n"
                    + "\n".join(f"- {s}" for s in prev_suggestions)
                )

        user_content = (
            f"RESEARCH QUESTION: {state['question']}\n\n"
            f"{dossier_block}{code_context}{retry_note}"
        )

        llm = get_llm(temperature=0.4)
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]

        full_text = ""
        try:
            async for chunk in llm.astream(messages):
                if chunk.content:
                    full_text += chunk.content
                    if token_cb:
                        await token_cb(chunk.content)
        except Exception as exc:
            logger.error("writer_stream_failed", error=str(exc))
            return {"answer": f"Error generating answer: {exc}", "follow_ups": []}

        # Extract follow-up questions from the answer
        follow_ups: list[str] = []
        if "Further Research Directions:" in full_text:
            section = full_text.split("Further Research Directions:")[-1]
            for line in section.strip().split("\n"):
                line = line.strip().lstrip("123456789. ").strip()
                if line and "?" in line:
                    follow_ups.append(line)
                if len(follow_ups) == 3:
                    break

        return {
            "answer": full_text,
            "follow_ups": follow_ups,
            "retry_count": state.get("retry_count", 0),
        }
