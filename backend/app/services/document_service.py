"""Document lifecycle: store → parse → chunk → embed → index → persist.

Reuses the existing embedding pipeline (FastEmbed) and Qdrant vector store.
Document chunks live in a dedicated Qdrant collection and are filterable by
``user_id`` and ``workspace_id`` so retrieval can scope to personal or
workspace documents.
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.document import Document, DocumentChunk
from app.services import document_parser, storage_service

logger = get_logger("noesis.documents")

SUPPORTED_KINDS = {"pdf", "docx", "txt", "markdown"}
_MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "markdown": "text/markdown",
}


def detect_kind(filename: str) -> str | None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "pdf": "pdf",
        "docx": "docx",
        "doc": "docx",
        "txt": "txt",
        "md": "markdown",
        "markdown": "markdown",
    }.get(ext)


async def create_document(
    db: AsyncSession,
    *,
    user_id: str,
    workspace_id: str | None,
    filename: str,
    data: bytes,
) -> Document:
    """Store the original, then parse/chunk/embed/index it synchronously."""
    kind = detect_kind(filename) or "txt"
    mime = _MIME.get(kind, "application/octet-stream")
    key = f"{storage_service.DOCUMENTS_PREFIX}/{user_id}/{uuid.uuid4().hex}_{filename}"

    doc = Document(
        user_id=user_id,
        workspace_id=workspace_id,
        filename=filename,
        mime_type=mime,
        file_size=len(data),
        kind=kind,
        status="processing",
    )
    db.add(doc)
    await db.flush()

    # Activity tracking.
    try:
        from datetime import datetime, timezone

        from sqlalchemy import update

        from app.db.models.user import User

        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_active_at=datetime.now(timezone.utc))
        )
    except Exception:  # pragma: no cover
        pass

    # 1) Persist original to MinIO (best-effort; failure is non-fatal to metadata).
    try:
        await asyncio.to_thread(storage_service.put_object, key, data, mime)
        doc.minio_key = key
    except Exception as exc:
        logger.warning("document_store_failed", error=str(exc))

    # 2) Extract + chunk.
    try:
        text = await asyncio.to_thread(document_parser.extract_text, filename, kind, data)
        chunks = document_parser.chunk_text(text)
    except Exception as exc:
        logger.error("document_parse_failed", error=str(exc))
        doc.status = "failed"
        doc.error = str(exc)[:500]
        await db.flush()
        return doc

    # 3) Embed + index in Qdrant, persist chunk rows.
    indexed = 0
    try:
        indexed = await _embed_and_index(db, doc, chunks)
        doc.status = "indexed"
        doc.chunk_count = indexed
    except Exception as exc:
        logger.error("document_index_failed", error=str(exc))
        doc.status = "failed"
        doc.error = str(exc)[:500]

    await db.flush()
    return doc


async def _embed_and_index(
    db: AsyncSession, doc: Document, chunks: list[str]
) -> int:
    if not chunks:
        return 0

    from app.retrieval.embedder import embed_texts
    from app.vector.qdrant_client import DOCUMENTS_COLLECTION, get_qdrant
    from qdrant_client import models as qmodels

    vectors = await asyncio.to_thread(embed_texts, chunks)
    client = get_qdrant()

    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        vector_id = uuid.uuid4().hex
        db.add(
            DocumentChunk(
                document_id=doc.id,
                workspace_id=doc.workspace_id,
                chunk_index=i,
                content=chunk,
                vector_id=vector_id,
            )
        )
        points.append(
            qmodels.PointStruct(
                id=vector_id,
                vector=vector,
                payload={
                    "document_id": doc.id,
                    "user_id": doc.user_id,
                    "workspace_id": doc.workspace_id,
                    "filename": doc.filename,
                    "chunk_index": i,
                    "content": chunk,
                },
            )
        )

    await client.upsert(collection_name=DOCUMENTS_COLLECTION, points=points)
    return len(points)


async def list_documents(
    db: AsyncSession, *, user_id: str, workspace_id: str | None = None
) -> list[Document]:
    q = select(Document).where(Document.user_id == user_id)
    if workspace_id:
        q = q.where(Document.workspace_id == workspace_id)
    q = q.order_by(Document.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_document(
    db: AsyncSession, *, document_id: str, user_id: str
) -> Document | None:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def delete_document(db: AsyncSession, *, document: Document) -> None:
    # Remove vectors from Qdrant.
    try:
        from app.vector.qdrant_client import DOCUMENTS_COLLECTION, get_qdrant
        from qdrant_client import models as qmodels

        client = get_qdrant()
        await client.delete(
            collection_name=DOCUMENTS_COLLECTION,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document.id),
                        )
                    ]
                )
            ),
        )
    except Exception as exc:
        logger.warning("document_vector_delete_failed", error=str(exc))

    # Remove original from MinIO.
    if document.minio_key:
        await asyncio.to_thread(storage_service.delete_object, document.minio_key)

    await db.delete(document)


async def search_documents(
    query: str,
    *,
    user_id: str,
    workspace_id: str | None = None,
    top_k: int = 10,
) -> list[dict]:
    """Dense search over the user's (or workspace's) document chunks."""
    try:
        from app.retrieval.embedder import embed_query
        from app.vector.qdrant_client import DOCUMENTS_COLLECTION, get_qdrant
        from qdrant_client import models as qmodels

        vector = await asyncio.to_thread(embed_query, query)
        must = [
            qmodels.FieldCondition(
                key="user_id", match=qmodels.MatchValue(value=user_id)
            )
        ]
        if workspace_id:
            must.append(
                qmodels.FieldCondition(
                    key="workspace_id",
                    match=qmodels.MatchValue(value=workspace_id),
                )
            )
        client = get_qdrant()
        response = await client.query_points(
            collection_name=DOCUMENTS_COLLECTION,
            query=vector,
            limit=top_k,
            query_filter=qmodels.Filter(must=must),
            with_payload=True,
        )
        hits = response.points
        return [
            {
                "id": f"doc:{h.payload.get('document_id')}:{h.payload.get('chunk_index')}",
                "title": h.payload.get("filename", "Document"),
                "abstract": h.payload.get("content", ""),
                "source": "document",
                "score": h.score,
            }
            for h in hits
            if h.payload
        ]
    except Exception as exc:
        # Surface the error type explicitly: a swallowed AttributeError here
        # (e.g. a removed client method) previously hid document RAG failures.
        logger.error(
            "document_search_failed",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return []
