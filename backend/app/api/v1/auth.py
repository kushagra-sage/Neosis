"""Auth routes.

  POST /auth/register                     — email+password signup
  POST /auth/login                        — OAuth2PasswordRequestForm (form or JSON)
  POST /auth/refresh                      — rotate refresh token
  POST /auth/logout                       — revoke refresh token
  GET  /auth/me                           — current user profile
  GET  /auth/me/stats                     — aggregated research stats
  GET  /auth/oauth/github                 — begin GitHub OAuth flow
  GET  /auth/oauth/github/callback        — exchange code, issue JWT, redirect to frontend
"""

from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    UserStatsResponse,
)
from app.security.dependencies import CurrentUser
from app.services import auth_service
from app.services.user_service import create_user, get_user_by_oauth

logger = get_logger("noesis.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


def _device_hint(request: Request) -> str | None:
    ua = request.headers.get("User-Agent", "")
    return ua[:120] if ua else None


# ── Email / Password ──────────────────────────────────────────────────────────


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    tokens = await auth_service.register(
        db,
        username=body.username,
        email=body.email,
        password=body.password,
        device_hint=_device_hint(request),
    )
    await db.commit()
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Accepts the OAuth2 password form (``username`` + ``password`` fields)."""
    tokens = await auth_service.login(
        db,
        username_or_email=form.username,
        password=form.password,
        device_hint=_device_hint(request),
    )
    await db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    tokens = await auth_service.refresh(
        db,
        raw_refresh_token=body.refresh_token,
        device_hint=_device_hint(request),
    )
    await db.commit()
    return tokens


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    body: LogoutRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await auth_service.logout(db, raw_refresh_token=body.refresh_token)
    await db.commit()
    return {"detail": "Logged out"}


# ── Current user ──────────────────────────────────────────────────────────────


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/me/stats", response_model=UserStatsResponse)
async def me_stats(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserStatsResponse:
    return await auth_service.user_stats(db, current_user.id)


# ── GitHub OAuth ──────────────────────────────────────────────────────────────


@router.get("/oauth/github", include_in_schema=bool(settings.github_client_id))
async def github_oauth_begin(request: Request) -> RedirectResponse:
    if not settings.github_client_id:
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured")
    callback_uri = f"{settings.oauth_backend_url}{settings.api_v1_prefix}/auth/oauth/github/callback"
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={callback_uri}"
        f"&scope=read:user+user:email"
    )
    return RedirectResponse(url)


@router.get("/oauth/github/callback", include_in_schema=bool(settings.github_client_id))
async def github_oauth_callback(
    code: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RedirectResponse:
    if not settings.github_client_id:
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured")

    # Exchange code for GitHub access token.
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret.get_secret_value(),
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
    if resp.status_code != 200:
        return RedirectResponse(f"{settings.oauth_frontend_url}/login?error=oauth_failed")

    gh_token = resp.json().get("access_token")
    if not gh_token:
        return RedirectResponse(f"{settings.oauth_frontend_url}/login?error=oauth_failed")

    # Fetch the GitHub user profile.
    async with httpx.AsyncClient(timeout=15) as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"},
        )
        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"},
        )

    gh_user = user_resp.json()
    gh_id = str(gh_user.get("id", ""))
    gh_login = gh_user.get("login", f"gh_{gh_id}")
    primary_email = next(
        (e["email"] for e in email_resp.json() if e.get("primary")),
        f"{gh_login}@github.noreply.com",
    )

    # Find or create the local user.
    user = await get_user_by_oauth(db, "github", gh_id)
    if user is None:
        # Use the GitHub login as username; append a suffix if taken.
        username = gh_login
        from app.services.user_service import get_user_by_username
        if await get_user_by_username(db, username):
            username = f"{gh_login}_{gh_id[:6]}"
        user = await create_user(
            db,
            username=username,
            email=primary_email,
            oauth_provider="github",
            oauth_id=gh_id,
        )

    tokens = await auth_service._issue_token_pair(db, user.id, _device_hint(request))
    await db.commit()

    redirect_url = (
        f"{settings.oauth_frontend_url}/oauth/callback"
        f"?access_token={tokens.access_token}"
        f"&refresh_token={tokens.refresh_token}"
    )
    return RedirectResponse(redirect_url)


# ── Google OAuth ──────────────────────────────────────────────────────────────


@router.get("/oauth/google", include_in_schema=bool(settings.google_client_id))
async def google_oauth_begin(request: Request) -> RedirectResponse:
    if not settings.google_client_id:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    callback_uri = f"{settings.oauth_backend_url}{settings.api_v1_prefix}/auth/oauth/google/callback"
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={callback_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=online"
        "&prompt=select_account"
    )
    return RedirectResponse(url)


@router.get("/oauth/google/callback", include_in_schema=bool(settings.google_client_id))
async def google_oauth_callback(
    code: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RedirectResponse:
    if not settings.google_client_id:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    callback_uri = f"{settings.oauth_backend_url}{settings.api_v1_prefix}/auth/oauth/google/callback"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret.get_secret_value(),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": callback_uri,
            },
            headers={"Accept": "application/json"},
        )
    if resp.status_code != 200:
        return RedirectResponse(f"{settings.oauth_frontend_url}/login?error=oauth_failed")

    g_token = resp.json().get("access_token")
    if not g_token:
        return RedirectResponse(f"{settings.oauth_frontend_url}/login?error=oauth_failed")

    async with httpx.AsyncClient(timeout=15) as client:
        user_resp = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {g_token}"},
        )
    if user_resp.status_code != 200:
        return RedirectResponse(f"{settings.oauth_frontend_url}/login?error=oauth_failed")

    g_user = user_resp.json()
    g_id = str(g_user.get("sub", ""))
    g_email = g_user.get("email") or f"{g_id}@google.noreply.com"
    g_name = g_user.get("name") or g_email.split("@")[0]
    if not g_id:
        return RedirectResponse(f"{settings.oauth_frontend_url}/login?error=oauth_failed")

    from app.services.user_service import get_user_by_email, get_user_by_username

    user = await get_user_by_oauth(db, "google", g_id)
    if user is None:
        existing = await get_user_by_email(db, g_email)
        if existing is not None:
            existing.oauth_provider = existing.oauth_provider or "google"
            existing.oauth_id = existing.oauth_id or g_id
            await db.flush()
            user = existing
        else:
            base = "".join(
                c for c in g_name.lower().replace(" ", "_") if c.isalnum() or c in "_-"
            )[:24] or f"user_{g_id[:6]}"
            username = base
            if await get_user_by_username(db, username):
                username = f"{base}_{g_id[:6]}"
            user = await create_user(
                db,
                username=username,
                email=g_email,
                oauth_provider="google",
                oauth_id=g_id,
            )

    tokens = await auth_service._issue_token_pair(db, user.id, _device_hint(request))
    await db.commit()

    return RedirectResponse(
        f"{settings.oauth_frontend_url}/oauth/callback"
        f"?access_token={tokens.access_token}"
        f"&refresh_token={tokens.refresh_token}"
    )


# ── Password reset ────────────────────────────────────────────────────────────


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Begin a password reset.

    Always returns 200 with a neutral message so the endpoint cannot be used to
    enumerate registered emails. When SMTP is unconfigured the caller is told the
    feature is temporarily unavailable.
    """
    result = await auth_service.begin_password_reset(db, email=body.email)
    await db.commit()
    if result == "unavailable":
        return {"detail": "Password reset temporarily unavailable.", "status": "unavailable"}
    return {
        "detail": "If an account exists for that email, a reset link has been sent.",
        "status": "ok",
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    body: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    ok = await auth_service.complete_password_reset(
        db, token=body.token, new_password=body.new_password
    )
    await db.commit()
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
    return {"detail": "Password updated. You can now sign in."}
