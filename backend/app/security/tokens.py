"""JWT creation and verification.

Access tokens carry a short TTL and are verified solely by the JWT signature.
Refresh tokens additionally carry a ``jti`` (JWT ID) claim — a random UUID
that is stored hashed in the database, enabling single-use rotation and
explicit revocation.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import settings


# ── Token creation ────────────────────────────────────────────────────────────


def _encode(payload: dict[str, Any]) -> str:
    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(user_id: str) -> str:
    """Return a short-lived access token for *user_id*."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_expiry_minutes
    )
    return _encode({"sub": user_id, "exp": expire, "type": "access"})


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    """Return ``(encoded_jwt, jti, expires_at)`` for a new refresh token.

    The caller is responsible for storing ``hash_jti(jti)`` in the database.
    """
    jti = uuid.uuid4().hex
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expiry_days)
    token = _encode({"sub": user_id, "exp": expire, "type": "refresh", "jti": jti})
    return token, jti, expire


def hash_jti(jti: str) -> str:
    """SHA-256 hex digest of a JTI — used as the DB lookup key."""
    return hashlib.sha256(jti.encode()).hexdigest()


# ── Token verification ────────────────────────────────────────────────────────


def decode_access_token(token: str) -> str:
    """Verify signature and expiry; return the ``sub`` (user_id) or raise.

    Raises :class:`jose.JWTError` on any validation failure.
    """
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    if payload.get("type") != "access":
        raise JWTError("Wrong token type")
    sub = payload.get("sub")
    if not sub:
        raise JWTError("Missing subject claim")
    return str(sub)


def decode_refresh_token(token: str) -> tuple[str, str]:
    """Verify signature and expiry; return ``(user_id, jti)`` or raise.

    Raises :class:`jose.JWTError` on any validation failure.
    """
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    if payload.get("type") != "refresh":
        raise JWTError("Wrong token type")
    sub = payload.get("sub")
    jti = payload.get("jti")
    if not sub or not jti:
        raise JWTError("Missing claims")
    return str(sub), str(jti)
