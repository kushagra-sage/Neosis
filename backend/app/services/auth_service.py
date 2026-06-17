"""Authentication service.

Implements:
  * ``register``   — create a user, issue initial token pair
  * ``login``      — verify credentials, issue token pair
  * ``refresh``    — rotate a refresh token (revoke old, issue new)
  * ``logout``     — revoke a refresh token
  * ``user_stats`` — aggregated stats for ``GET /auth/me/stats``
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import get_logger
from app.db.models.auth import RefreshToken
from app.db.models.inquiry import Inquiry
from app.db.models.library import Paper
from app.db.models.research import LiteratureReview
from app.db.models.workspace import Workspace
from app.schemas.auth import TokenResponse, UserStatsResponse
from app.security.hashing import hash_password, verify_password
from app.security.tokens import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_jti,
)
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)

logger = get_logger("noesis.auth")


# ── Token pair helpers ────────────────────────────────────────────────────────


async def _issue_token_pair(
    db: AsyncSession,
    user_id: str,
    device_hint: str | None = None,
) -> TokenResponse:
    """Create a new access + refresh token pair and persist the refresh token."""
    access = create_access_token(user_id)
    refresh, jti, expires_at = create_refresh_token(user_id)

    rt = RefreshToken(
        user_id=user_id,
        token_hash=hash_jti(jti),
        expires_at=expires_at,
        device_hint=device_hint,
    )
    db.add(rt)
    await db.flush()

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_expiry_minutes * 60,
    )


# ── Public API ────────────────────────────────────────────────────────────────


async def register(
    db: AsyncSession,
    *,
    username: str,
    email: str,
    password: str,
    device_hint: str | None = None,
) -> TokenResponse:
    if await get_user_by_username(db, username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )
    if await get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = await create_user(
        db,
        username=username,
        email=email,
        hashed_password=hash_password(password),
    )
    tokens = await _issue_token_pair(db, user.id, device_hint)
    logger.info("user_registered", user_id=user.id, username=username)
    return tokens


async def login(
    db: AsyncSession,
    *,
    username_or_email: str,
    password: str,
    device_hint: str | None = None,
) -> TokenResponse:
    # Accept both username and email as the identifier.
    if "@" in username_or_email:
        user = await get_user_by_email(db, username_or_email)
    else:
        user = await get_user_by_username(db, username_or_email)

    _INVALID = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise _INVALID
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account deactivated")
    if user.hashed_password is None:
        # OAuth-only account — direct password login is not allowed.
        raise HTTPException(
            status_code=400,
            detail=f"This account uses {user.oauth_provider or 'social'} login",
        )
    if not verify_password(password, user.hashed_password):
        raise _INVALID

    tokens = await _issue_token_pair(db, user.id, device_hint)
    user.last_active_at = datetime.now(timezone.utc)
    logger.info("user_login", user_id=user.id)
    return tokens


async def refresh(
    db: AsyncSession,
    *,
    raw_refresh_token: str,
    device_hint: str | None = None,
) -> TokenResponse:
    """Atomically revoke *raw_refresh_token* and return a fresh pair."""
    _INVALID = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
    )
    try:
        user_id, jti = decode_refresh_token(raw_refresh_token)
    except JWTError:
        raise _INVALID

    token_hash = hash_jti(jti)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()

    if stored is None or stored.revoked:
        raise _INVALID
    if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise _INVALID

    # Revoke the consumed token.
    stored.revoked = True
    await db.flush()

    new_tokens = await _issue_token_pair(db, user_id, device_hint)
    logger.info("token_refreshed", user_id=user_id)
    return new_tokens


async def logout(db: AsyncSession, *, raw_refresh_token: str) -> None:
    """Revoke a single refresh token. No-op if already revoked / not found."""
    try:
        _, jti = decode_refresh_token(raw_refresh_token)
    except JWTError:
        return  # Treat malformed token as a silent no-op on logout

    token_hash = hash_jti(jti)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()
    if stored and not stored.revoked:
        stored.revoked = True
        await db.flush()


async def user_stats(db: AsyncSession, user_id: str) -> UserStatsResponse:
    """Return aggregate counts for the authenticated user."""

    async def _count(model, *where):  # type: ignore[type-arg]
        result = await db.execute(
            select(func.count()).select_from(model).where(*where)
        )
        return result.scalar_one()

    from app.db.models.user import User

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    workspaces = await _count(Workspace, Workspace.user_id == user_id)
    papers = await _count(Paper, Paper.workspace_id.in_(
        select(Workspace.id).where(Workspace.user_id == user_id).scalar_subquery()
    ))
    inquiries = await _count(Inquiry, Inquiry.user_id == user_id)
    reviews = await _count(
        LiteratureReview,
        LiteratureReview.workspace_id.in_(
            select(Workspace.id).where(Workspace.user_id == user_id).scalar_subquery()
        ),
    )

    return UserStatsResponse(
        total_workspaces=workspaces,
        total_papers=papers,
        total_inquiries=inquiries,
        reviews_generated=reviews,
        member_since=user.created_at,
    )


# ── Password reset ────────────────────────────────────────────────────────────


async def begin_password_reset(db: AsyncSession, *, email: str) -> str:
    """Create a reset token and dispatch it.

    Returns ``"ok"`` when a token was created (or silently skipped for an unknown
    email — we never reveal which), or ``"unavailable"`` when no email transport
    is configured so the caller cannot actually receive the link.
    """
    import hashlib
    import secrets
    from datetime import timedelta

    from app.db.models.password_reset import PasswordResetToken
    from app.services.email_service import send_password_reset_email, email_available

    if not email_available():
        return "unavailable"

    user = await get_user_by_email(db, email)
    # Always behave the same whether or not the user exists.
    if user is not None and user.hashed_password is not None:
        raw = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        expires = datetime.now(timezone.utc) + timedelta(
            minutes=settings.reset_token_expiry_minutes
        )
        db.add(
            PasswordResetToken(
                user_id=user.id, token_hash=token_hash, expires_at=expires, used=False
            )
        )
        await db.flush()
        reset_link = f"{settings.oauth_frontend_url}/reset-password?token={raw}"
        await send_password_reset_email(user.email, reset_link)

    return "ok"


async def complete_password_reset(
    db: AsyncSession, *, token: str, new_password: str
) -> bool:
    import hashlib

    from app.db.models.password_reset import PasswordResetToken

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        return False

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return False

    user_result = await db.execute(select(User).where(User.id == record.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return False

    user.hashed_password = hash_password(new_password)
    record.used = True

    # Revoke all active refresh tokens for safety.
    tokens = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False)
        )
    )
    for t in tokens.scalars().all():
        t.revoked = True

    await db.flush()
    logger.info("password_reset_completed", user_id=user.id)
    return True
