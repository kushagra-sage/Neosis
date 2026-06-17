"""Pydantic schemas for the auth endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if v.isdigit() or v.isalpha():
            raise ValueError("Password must contain both letters and numbers")
        return v


class LoginRequest(BaseModel):
    """Used by the JSON login endpoint (not the OAuth2 form endpoint)."""
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token TTL in seconds


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    oauth_provider: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserStatsResponse(BaseModel):
    total_workspaces: int
    total_papers: int
    total_inquiries: int
    reviews_generated: int
    member_since: datetime


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=16, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password_complexity(cls, v: str) -> str:
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("Password must contain both letters and numbers")
        return v
