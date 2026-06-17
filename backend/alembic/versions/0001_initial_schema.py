"""Initial schema — all Noesis tables.

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(32), nullable=False),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column("hashed_password", sa.String(256), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("oauth_provider", sa.String(32), nullable=True),
        sa.Column("oauth_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_oauth_id", "users", ["oauth_id"])

    # ── refresh_tokens ─────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("device_hint", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_revoked", "refresh_tokens", ["revoked"])
    op.create_index("ix_refresh_tokens_user_revoked", "refresh_tokens", ["user_id", "revoked"])

    # ── workspaces ─────────────────────────────────────────────────────────────
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False, server_default="custom"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workspaces_user_id", "workspaces", ["user_id"])
    op.create_index("ix_workspaces_user_id_slug", "workspaces", ["user_id", "slug"], unique=True)
    op.create_index("ix_workspaces_user_id_updated_at", "workspaces", ["user_id", "updated_at"])

    # ── papers ─────────────────────────────────────────────────────────────────
    op.create_table(
        "papers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("venue", sa.String(256), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="upload"),
        sa.Column("external_id", sa.String(128), nullable=True),
        sa.Column("doi", sa.String(128), nullable=True),
        sa.Column("arxiv_id", sa.String(64), nullable=True),
        sa.Column("url", sa.String(1024), nullable=True),
        sa.Column("citation_count", sa.Integer(), nullable=True),
        sa.Column("minio_key", sa.String(512), nullable=True),
        sa.Column("indexed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("qdrant_point_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("extra", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_papers_workspace_id", "papers", ["workspace_id"])
    op.create_index("ix_papers_external_id", "papers", ["external_id"])
    op.create_index("ix_papers_doi", "papers", ["doi"])
    op.create_index("ix_papers_indexed", "papers", ["indexed"])
    op.create_index("ix_papers_workspace_created", "papers", ["workspace_id", "created_at"])

    # ── notes ──────────────────────────────────────────────────────────────────
    op.create_table(
        "notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paper_id", sa.String(36), sa.ForeignKey("papers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(256), nullable=True),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notes_workspace_id", "notes", ["workspace_id"])
    op.create_index("ix_notes_paper_id", "notes", ["paper_id"])

    # ── research_questions ─────────────────────────────────────────────────────
    op.create_table(
        "research_questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="open"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_questions_workspace_id", "research_questions", ["workspace_id"])

    # ── experiments ────────────────────────────────────────────────────────────
    op.create_table(
        "experiments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="planned"),
        sa.Column("plan", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_experiments_workspace_id", "experiments", ["workspace_id"])

    # ── literature_reviews ─────────────────────────────────────────────────────
    op.create_table(
        "literature_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("citations", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("critic_scores", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_literature_reviews_workspace_id", "literature_reviews", ["workspace_id"])
    op.create_index("ix_reviews_workspace_created", "literature_reviews", ["workspace_id", "created_at"])

    # ── research_gaps ──────────────────────────────────────────────────────────
    op.create_table(
        "research_gaps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(24), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_gaps_workspace_id", "research_gaps", ["workspace_id"])

    # ── future_ideas ───────────────────────────────────────────────────────────
    op.create_table(
        "future_ideas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_future_ideas_workspace_id", "future_ideas", ["workspace_id"])

    # ── timeline_events ────────────────────────────────────────────────────────
    op.create_table(
        "timeline_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("ref_id", sa.String(36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_timeline_events_workspace_id", "timeline_events", ["workspace_id"])
    op.create_index("ix_timeline_workspace_created", "timeline_events", ["workspace_id", "created_at"])

    # ── research_memories ──────────────────────────────────────────────────────
    op.create_table(
        "research_memories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding_id", sa.String(64), nullable=True),
        sa.Column("source_ref", sa.String(36), nullable=True),
        sa.Column("salience", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("extra", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_memories_user_id", "research_memories", ["user_id"])
    op.create_index("ix_research_memories_workspace_id", "research_memories", ["workspace_id"])
    op.create_index("ix_memories_user_workspace_kind", "research_memories", ["user_id", "workspace_id", "kind"])
    op.create_index("ix_memories_user_created", "research_memories", ["user_id", "created_at"])

    # ── inquiries ──────────────────────────────────────────────────────────────
    op.create_table(
        "inquiries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("inquiry_type", sa.String(32), nullable=True),
        sa.Column("output_mode", sa.Text(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("plan", sa.JSON(), nullable=True),
        sa.Column("dossier", sa.JSON(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("critic_scores", sa.JSON(), nullable=True),
        sa.Column("follow_ups", sa.JSON(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_inquiries_user_id", "inquiries", ["user_id"])
    op.create_index("ix_inquiries_workspace_id", "inquiries", ["workspace_id"])
    op.create_index("ix_inquiries_status", "inquiries", ["status"])
    op.create_index("ix_inquiries_user_created", "inquiries", ["user_id", "created_at"])
    op.create_index("ix_inquiries_workspace_created", "inquiries", ["workspace_id", "created_at"])


def downgrade() -> None:
    for table in [
        "inquiries", "research_memories", "timeline_events", "future_ideas",
        "research_gaps", "literature_reviews", "experiments", "research_questions",
        "notes", "papers", "workspaces", "refresh_tokens", "users",
    ]:
        op.drop_table(table)
