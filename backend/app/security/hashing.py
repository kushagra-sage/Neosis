"""bcrypt password hashing helpers.

A single CryptContext is module-level so the bcrypt cost factor is computed
once and the context is reused across requests.
"""

from __future__ import annotations

from passlib.context import CryptContext

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    return _ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return _ctx.verify(plain, hashed)
