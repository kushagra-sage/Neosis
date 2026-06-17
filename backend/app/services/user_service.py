"""Async CRUD helpers for the User model."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(
        select(User).where(func.lower(User.username) == username.lower())
    )
    return result.scalar_one_or_none()


async def get_user_by_oauth(
    db: AsyncSession, provider: str, oauth_id: str
) -> User | None:
    result = await db.execute(
        select(User).where(User.oauth_provider == provider, User.oauth_id == oauth_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    username: str,
    email: str,
    hashed_password: str | None = None,
    oauth_provider: str | None = None,
    oauth_id: str | None = None,
) -> User:
    user = User(
        username=username,
        email=email.lower(),
        hashed_password=hashed_password,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
    )
    db.add(user)
    await db.flush()  # assigns id without committing
    return user
