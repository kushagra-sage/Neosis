<div align="center">

# Noesis

### Research Intelligence OS
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)]()

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)]()

[![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&logoColor=white)]()

[![LangChain](https://img.shields.io/badge/LangChain-Latest-1C3C3C)]()

[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-FF6B35)]()

[![arXiv](https://img.shields.io/badge/arXiv-Scholarly_Search-B31B1B)]()

[![Semantic Scholar](https://img.shields.io/badge/Semantic_Scholar-Research_API-1857B6)]()

[![OpenAlex](https://img.shields.io/badge/OpenAlex-Academic_Graph-00A86B)]()

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)]()

[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)]()

[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-BA55D3)]()

[![MinIO](https://img.shields.io/badge/MinIO-Object_Storage-C72E29)]()

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)]()

[![License](https://img.shields.io/badge/License-MIT-yellow)]()

**From a research question to a peer-reviewed, evidence-grounded answer — automatically.**

Noesis is a multi-agent research copilot. Ask it a question and it plans the inquiry,
retrieves evidence from the world's scholarly corpora *and your own documents*,
synthesises a cited answer, and then peer-reviews its own rigor before showing you anything.

</div>

---

## Vision

Literature review is slow, fragmented, and hard to trust. Keyword search misses
cross-disciplinary work; chat models invent citations; and a fluent answer looks
identical to a correct one until you check every source by hand. Noesis treats a
research question the way a careful researcher does — decompose, gather evidence,
reason, write, and critique — and runs that process as a transparent pipeline of
specialised agents with an automated peer-review gate.

## Platform overview

- **Multi-agent pipeline** — Planner → Retriever → Analyst → Writer → Reviewer, orchestrated as a LangGraph state machine with a self-review retry loop.
- **Hybrid retrieval** — dense vectors + BM25 + arXiv + Semantic Scholar + OpenAlex + *your uploaded documents*, fused with Reciprocal Rank Fusion.
- **Document RAG** — upload PDFs, DOCX, TXT, and Markdown; they're parsed, chunked, embedded, indexed in Qdrant, and searched alongside scholarly sources.
- **Workspaces** — organise papers, notes, gaps, experiments, and inquiry history by research line.
- **Automated peer review** — every answer scored on groundedness, citation accuracy, coverage, and rigor.
- **Admin analytics** — user / research / document / workspace / system dashboards with CSV & JSON export.
- **Auth** — email/password, GitHub OAuth, Google OAuth, JWT with refresh-token rotation, and a secure password-reset flow.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Frontend — Next.js 14 (App Router, TS, Tailwind, Zustand, RQ)     │
│  Landing · Auth (+OAuth) · Workspaces · Console · Admin · Settings │
└───────────────┬──────────────────────────────────┬─────────────────┘
        REST (axios)                       WS /ws/inquiry
                │                                  │
┌───────────────▼──────────────────────────────────▼─────────────────┐
│  API Gateway — FastAPI                                             │
│  JWT auth · rate limiting · CORS · request-id · OpenAPI docs       │
└───────────────┬────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────┐
│  Agent Pipeline — LangGraph StateGraph                             │
│  Planner → Retriever → Analyst → Writer → Reviewer (+ retry edge)  │
│  Resilience: circuit breakers · bulkheads · sagas · retries        │
└──────┬───────────────────┬───────────────────────┬─────────────────┘
       │                   │                        │
┌──────▼──────┐   ┌────────▼────────┐   ┌───────────▼────────────┐
│ Retrieval   │   │ Data layer      │   │ External + documents    │
│ FastEmbed   │   │ PostgreSQL 16   │   │ arXiv · S2 · OpenAlex   │
│ BM25Okapi   │   │ Redis 7         │   │ Qdrant (papers + docs)  │
│ RRF (k=60)  │   │ Qdrant · MinIO  │   │ MinIO (originals)       │
└─────────────┘   └─────────────────┘   └─────────────────────────┘
```

### Multi-agent workflow

| Operator | Responsibility |
| -------- | -------------- |
| **Planner** | Decomposes the question, classifies the inquiry type, routes the pipeline. |
| **Retriever** | Hybrid search across local corpus, uploaded documents, and three scholarly APIs; fuses via RRF. |
| **Analyst** | Runs sandboxed computation when the question needs statistics. |
| **Writer** | Streams a grounded synthesis citing only the retrieved dossier. |
| **Reviewer** | Scores groundedness, citation accuracy, coverage, rigor; gates publication and triggers one revision. |

---

## Authentication

JWT access tokens with rotating refresh tokens (each refresh token is stored as a
SHA-256 hash and single-use). Three sign-in methods:

- **Email / password** — `POST /auth/login` (OAuth2 password form).
- **GitHub OAuth** — `GET /auth/oauth/github` → callback → `/oauth/callback?access_token&refresh_token`.
- **Google OAuth** — `GET /auth/oauth/google` → callback, same redirect contract.

### Google OAuth

Mirrors the GitHub flow exactly. The begin route redirects to Google's consent
screen; the callback exchanges the code at `oauth2.googleapis.com/token`, fetches
the profile from `openidconnect.googleapis.com/v1/userinfo`, then **matches by
Google ID → links an existing email account → or creates a new user**, reusing the
shared JWT/refresh issuance. Configure `GOOGLE_CLIENT_ID` and
`GOOGLE_CLIENT_SECRET`; the frontend "Continue with Google" button targets the
backend begin route.

### Forgot / reset password

- `POST /auth/forgot-password` — always returns 200 with a neutral message (no email enumeration); responds `unavailable` when SMTP isn't configured so the UI shows *"Password reset temporarily unavailable"* instead of failing.
- `POST /auth/reset-password` — validates a single-use, time-limited token (SHA-256 hashed at rest), sets the new password, and revokes all active refresh tokens.

---

## Document upload & RAG

Upload via `POST /documents/upload` (multipart; PDF / DOCX / TXT / Markdown, ≤25 MB).
Lifecycle: **store original in MinIO → extract text → chunk (1200 chars, 150 overlap)
→ embed with FastEmbed → index in a dedicated Qdrant collection → persist metadata
and chunk rows in PostgreSQL.** Documents are filterable by `user_id` and
`workspace_id`, and are searched as a first-class source inside the existing inquiry
pipeline — no separate research system.

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/documents/upload` | Multipart upload + processing |
| GET | `/documents` | List caller's documents (`?workspace_id`) |
| GET | `/documents/{id}` | Document detail |
| DELETE | `/documents/{id}` | Remove document, vectors, and original |

---

## Admin dashboard & analytics

Admin access is granted to usernames/emails listed in `ADMIN_EMAILS`. The `/admin`
UI shows KPI cards, dependency-free SVG charts (user growth, query volume, uploads,
workspace growth), and tables (recent users, most active workspaces), with range
filters (24h / 7d / 30d / 90d / all) and CSV / JSON export.

| Endpoint | Returns |
| -------- | ------- |
| `GET /admin/analytics/overview` | Totals, DAU/WAU/MAU, growth rate, storage |
| `GET /admin/analytics/users` | Daily signups + recent users |
| `GET /admin/analytics/workspaces` | Daily created + most active |
| `GET /admin/analytics/documents` | Daily uploads, by-kind, storage |
| `GET /admin/analytics/inquiries` | Daily volume, avg latency, by-status |
| `GET /admin/analytics/system` | Redis/Qdrant health, error rate |

User activity (`last_active_at`) is recorded automatically on login, inquiry
creation, and document upload, powering the DAU/WAU/MAU metrics.

---

## Literature Review mode

A dedicated workflow (separate from single inquiries) that produces a structured,
fully-cited review. Generate one from a workspace with `POST /workspaces/{id}/reviews`
(topic in the body). The service retrieves a broad evidence base via the existing
hybrid retriever (documents + scholarly sources), clusters the literature into
themes, detects consensus and disagreement, surfaces gaps, and synthesizes a review
with these sections: **Introduction · Current State of Research · Key Findings ·
Conflicting Evidence · Research Gaps · Future Directions · References**. Each review
is self-reviewed (groundedness/coverage/rigor) and persisted as a `LiteratureReview`.

| Method | Path |
| ------ | ---- |
| POST | `/workspaces/{id}/reviews` |
| GET | `/workspaces/{id}/reviews` |
| GET | `/workspaces/{id}/reviews/{review_id}` |
| DELETE | `/workspaces/{id}/reviews/{review_id}` |

## Export system

Research answers and literature reviews export to **PDF, DOCX, Markdown, and
BibTeX**, with citations preserved in every format. PDF uses reportlab (pure-Python,
no system dependencies); DOCX uses python-docx; Markdown and BibTeX are rendered
directly. A shared `ExportDocument` drives one rendering path for all artefact types.

| Method | Path |
| ------ | ---- |
| GET | `/export/inquiry/{id}?format=pdf\|docx\|markdown\|bibtex` |
| GET | `/workspaces/{id}/reviews/{review_id}/export?format=...` |

## Database migrations

Alembic is the **single source of truth** for the schema in every environment.
The container entrypoint runs `alembic upgrade head` before serving, so the API
never starts against a half-migrated database.

```bash
alembic upgrade head      # apply all pending migrations
alembic current           # show the current revision
alembic downgrade -1      # roll back one revision
```

`create_all()` is **not** used for schema management. It is gated behind
`DB_AUTO_CREATE=true` (off by default, dev-only) purely for disposable local
databases; it bypasses Alembic and must never be enabled in production. Migration
`0003` is an idempotent repair that adds `users.display_name` / `users.last_active_at`
only if missing, fixing databases that drifted from a prior `create_all()` start.

## Database architecture

PostgreSQL 16 (asyncpg) with Alembic migrations. Core tables include `users`
(now with `display_name`, `last_active_at`), `refresh_tokens`,
`password_reset_tokens`, `workspaces`, `papers`, `notes`, research entities,
`inquiries`, and the new `documents` / `document_chunks`. Migration `0002` adds the
document tables, reset tokens, and the user activity columns.

## Retrieval architecture

Abstracts and document chunks are embedded with FastEmbed (`BAAI/bge-small-en-v1.5`,
384-dim ONNX) and stored in Qdrant (`noesis_papers`, `noesis_papers_documents`,
`noesis_papers_memory`). The Retriever runs all sources in parallel and fuses ranked
lists with Reciprocal Rank Fusion: `score(d) = Σ 1/(k + rank_i(d))`, `k = 60`.

---

## Docker setup

`docker compose up --build` brings up Postgres, Redis, Qdrant, MinIO, the FastAPI
backend, and the Next.js frontend.

| Service | URL |
| ------- | --- |
| Frontend | http://localhost:3000 |
| API + docs | http://localhost:8000/docs |
| Qdrant | http://localhost:6333/dashboard |
| MinIO | http://localhost:9001 |

## Development setup

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

## Environment variables

**Backend** (`.env`): `JWT_SECRET_KEY`, `DATABASE_URL`/`POSTGRES_*`, `REDIS_*`,
`QDRANT_*`, `MINIO_*`, `GITHUB_CLIENT_ID/SECRET`, **`GOOGLE_CLIENT_ID/SECRET`**,
`OAUTH_FRONTEND_URL`, `OAUTH_BACKEND_URL`, **`SMTP_HOST/PORT/USER/PASSWORD/FROM`**,
`RESET_TOKEN_EXPIRY_MINUTES`, **`ADMIN_EMAILS`**, `SEMANTIC_SCHOLAR_API_KEY` (optional).

**Frontend** (`.env.local`): `NEXT_PUBLIC_API_BASE_URL`, optional
`NEXT_PUBLIC_GITHUB_OAUTH_URL`, `NEXT_PUBLIC_GOOGLE_OAUTH_URL`.

## API reference

Base path `/api/v1`. Auth, workspaces, inquiries, library, **documents**, and
**admin** routers; full interactive docs at `/docs`.

## WebSocket overview

`WS /api/v1/ws/inquiry?token=<JWT>&workspace_id=<id>` — client sends
`{ "question": "…" }`; server streams `stage`, `token`, `dossier`, `critic`,
`done`, and `error` events.

---

## Future roadmap

- Read-only admin user-impersonation for support.
- Collaborative shared workspaces with roles.
- Citation graph visualisation across the dossier.

---

<div align="center">
<sub>Built for researchers who want answers they can cite.</sub>
</div>
