"""FastAPI security dependencies.

``CurrentUser``       — requires a valid access token; raises 401 otherwise.
``CurrentActiveUser`` — same, plus asserts ``is_active=True``.
``OptionalUser``      — returns ``None`` when no (or invalid) token is sent.
These are used as ``Depends(...)`` annotations throughout the API routes.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.session import get_db
from app.security.tokens import decode_access_token

# ``auto_error=False`` means a missing header returns ``None`` instead of 401,
# allowing ``OptionalUser`` to work without boilerplate.
_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _user_from_token(
    token: str | None,
    db: AsyncSession,
) -> User | None:
    """Decode *token* and return the matching active User, or None."""
    if not token:
        return None
    try:
        user_id = decode_access_token(token)
    except JWTError:
        return None

    from app.services.user_service import get_user_by_id  # local to avoid circular

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(
    token: Annotated[str | None, Depends(_oauth2)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await _user_from_token(token, db)
    if user is None:
        raise _CREDENTIALS_EXCEPTION
    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_optional_user(
    token: Annotated[str | None, Depends(_oauth2)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    return await _user_from_token(token, db)


# Convenience type aliases for use in route signatures.
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def get_admin_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require the caller to be an admin (username or email in ADMIN_EMAILS)."""
    from app.config import settings

    admins = settings.admin_email_list
    identity = {user.email.lower(), user.username.lower()}
    if not admins or identity.isdisjoint(admins):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


AdminUser = Annotated[User, Depends(get_admin_user)]
