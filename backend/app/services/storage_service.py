"""MinIO object storage helper for uploaded documents."""

from __future__ import annotations

import io

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("noesis.storage")

DOCUMENTS_PREFIX = "documents"


def _client():  # type: ignore[no-untyped-def]
    from minio import Minio

    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key.get_secret_value(),
        secure=settings.minio_secure,
    )


def put_object(key: str, data: bytes, content_type: str) -> str:
    """Store bytes in MinIO and return the object key."""
    client = _client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)
    client.put_object(
        settings.minio_bucket,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return key


def get_object(key: str) -> bytes:
    client = _client()
    resp = client.get_object(settings.minio_bucket, key)
    try:
        return resp.read()
    finally:
        resp.close()
        resp.release_conn()


def delete_object(key: str) -> None:
    try:
        _client().remove_object(settings.minio_bucket, key)
    except Exception as exc:  # pragma: no cover
        logger.warning("minio_delete_failed", key=key, error=str(exc))
