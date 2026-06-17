"""Central configuration for the Noesis backend.

All runtime configuration is sourced from environment variables (or a local
``.env`` file in development) and validated by Pydantic. A single cached
``Settings`` instance is exposed as ``settings`` so callers can simply do::

    from app.config import settings

Settings are grouped by concern. Computed properties build the connection
strings that SQLAlchemy / Redis / Qdrant expect, so individual components
(host, port, user, password) can be supplied independently in compose files
while still yielding a single DSN.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "Noesis"
    app_env: Literal["development", "staging", "production"] = "development"

    # Schema management. Alembic is the single source of truth for the schema in
    # ALL environments. This flag only exists for throwaway local/test databases
    # and is OFF by default so create_all() can never silently diverge from
    # Alembic (which is what caused the 0002 user-column drift). Leave it false
    # and run `alembic upgrade head` instead.
    db_auto_create: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_json: bool = False  # ConsoleRenderer in dev, JSON in prod

    # ── Security / CORS ───────────────────────────────────────────────────────
    # Comma-separated list, e.g. "http://localhost:3000,https://noesis.app"
    cors_origins: str = "http://localhost:3000"
    jwt_secret_key: SecretStr = SecretStr("change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_expiry_minutes: int = 60
    jwt_refresh_expiry_days: int = 7

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "noesis"
    postgres_user: str = "noesis"
    postgres_password: SecretStr = SecretStr("noesis")
    # If set, overrides the computed DSN entirely (e.g. a managed Neon URL).
    database_url_override: str = ""
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: SecretStr = SecretStr("")
    redis_url_override: str = ""

    # ── Qdrant (vector store) ─────────────────────────────────────────────────
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_api_key: SecretStr = SecretStr("")
    qdrant_prefer_grpc: bool = False
    qdrant_collection: str = "noesis_papers"
    # BAAI/bge-small-en-v1.5 emits 384-dim vectors; bump to 768 for SPECTER2.
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    vector_distance: Literal["Cosine", "Dot", "Euclid"] = "Cosine"

    # ── LLM (Groq) ────────────────────────────────────────────────────────────
    groq_api_key: SecretStr = SecretStr("")
    groq_model: str = "llama-3.3-70b-versatile"

    # ── MinIO (object store) ─────────────────────────────────────────────────
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "noesis"
    minio_secret_key: SecretStr = SecretStr("noesis-secret")
    minio_bucket: str = "noesis-papers"
    minio_secure: bool = False

    # ── OAuth (social login) ──────────────────────────────────────────────────
    github_client_id: str = ""
    github_client_secret: SecretStr = SecretStr("")
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    # Where to redirect after a successful OAuth exchange.
    oauth_frontend_url: str = "http://localhost:3000"
    # Public URL of this backend — used to build the OAuth callback URIs.
    oauth_backend_url: str = "http://localhost:8000"

    # ── Password reset / email ────────────────────────────────────────────────
    reset_token_expiry_minutes: int = 30
    # SMTP is optional; when unset the reset flow degrades gracefully and the UI
    # is told the feature is temporarily unavailable.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_from: str = "noreply@noesis.app"

    # ── Admin ─────────────────────────────────────────────────────────────────
    # Comma-separated list of usernames or emails granted admin access.
    admin_emails: str = ""

    # ── Rate limiting ─────────────────────────────────────────────────────────
    rate_limit_requests: int = 60      # requests per window per authenticated user
    rate_limit_window_seconds: int = 60
    guest_query_limit: int = 5         # total queries per day for unauthenticated IPs
    guest_query_window_seconds: int = 86_400

    # ── Scholarly retrieval (Phase 2) ─────────────────────────────────────────
    semantic_scholar_api_key: SecretStr = SecretStr("")  # optional, raises rate limit
    retriever_top_k: int = 10
    retriever_rrf_k: int = 60

    # ── Computed connection strings ───────────────────────────────────────────
    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Async SQLAlchemy DSN (asyncpg driver)."""
        if self.database_url_override:
            return self.database_url_override
        pw = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{pw}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url_sync(self) -> str:
        """Sync DSN (psycopg) — used by Alembic migrations."""
        if self.database_url_override:
            return self.database_url_override.replace("+asyncpg", "+psycopg")
        pw = self.postgres_password.get_secret_value()
        return (
            f"postgresql+psycopg://{self.postgres_user}:{pw}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        if self.redis_url_override:
            return self.redis_url_override
        pw = self.redis_password.get_secret_value()
        auth = f":{pw}@" if pw else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_email_list(self) -> list[str]:
        """Usernames or emails granted admin access (lowercased)."""
        return [a.strip().lower() for a in self.admin_emails.split(",") if a.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate_runtime_secrets(self) -> None:
        """Fail fast in production when required secrets are placeholders."""
        if not self.is_production:
            return
        problems: list[str] = []
        if self.jwt_secret_key.get_secret_value() in ("", "change-me-in-production"):
            problems.append("JWT_SECRET_KEY")
        if not self.groq_api_key.get_secret_value():
            problems.append("GROQ_API_KEY")
        if self.postgres_password.get_secret_value() in ("", "noesis"):
            problems.append("POSTGRES_PASSWORD")
        if problems:
            raise RuntimeError(
                "Insecure/missing production secrets: " + ", ".join(problems)
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Convenience singleton.
settings: Settings = get_settings()
