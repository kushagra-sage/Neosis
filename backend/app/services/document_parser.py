"""Extract plain text from uploaded documents and split into chunks."""

from __future__ import annotations

import io

from app.core.logging import get_logger

logger = get_logger("noesis.docparser")

CHUNK_SIZE = 1200       # characters
CHUNK_OVERLAP = 150


def extract_text(filename: str, kind: str, data: bytes) -> str:
    """Best-effort text extraction by document kind."""
    if kind in ("txt", "markdown"):
        return data.decode("utf-8", errors="replace")

    if kind == "pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            return "\n\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:
            logger.warning("pdf_extract_failed", error=str(exc))
            return ""

    if kind == "docx":
        try:
            import docx  # python-docx

            document = docx.Document(io.BytesIO(data))
            return "\n".join(p.text for p in document.paragraphs)
        except Exception as exc:
            logger.warning("docx_extract_failed", error=str(exc))
            return ""

    return data.decode("utf-8", errors="replace")


def chunk_text(text: str) -> list[str]:
    """Sliding-window character chunks with overlap, split on whitespace."""
    text = " ".join(text.split())
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + CHUNK_SIZE, n)
        # Prefer to break on a space near the window edge.
        if end < n:
            space = text.rfind(" ", start + CHUNK_SIZE - 200, end)
            if space > start:
                end = space
        chunks.append(text[start:end].strip())
        if end >= n:
            break
        start = end - CHUNK_OVERLAP
    return [c for c in chunks if c]
