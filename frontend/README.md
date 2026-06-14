<div align="center">

# Noesis

### Research Intelligence OS

**From a research question to a peer-reviewed, evidence-grounded answer — automatically.**

Noesis is a multi-agent research copilot. Ask it a question and it plans the inquiry,
retrieves evidence from the world's scholarly corpora, synthesises a cited answer, and
then *peer-reviews its own rigor* before showing you anything.

[Architecture](#architecture) · [Quickstart](#local-development) · [API](#api-overview) · [Roadmap](#roadmap)

</div>

---

## What is Noesis?

Noesis treats a research question the way a careful researcher does: it is not a single
prompt to a language model, but a **process** — decompose, gather evidence, reason,
write, and critique. Noesis runs that process as a pipeline of five specialised agents
("operators") orchestrated as a directed graph, with a self-review loop that gates every
answer on four dimensions of academic rigor.

The result is an answer you can trust: every claim carries an inline citation back to a
real paper, and the system tells you how confident it is and where it fell short.

### The problem

Literature review is slow, fragmented, and hard to trust:

- **Search is shallow.** Keyword search over a single database misses the cross-disciplinary
  work that matters, and ranking by citation count buries recent breakthroughs.
- **LLMs hallucinate citations.** A raw chat model will happily invent a plausible-looking
  reference. For research that is worse than useless.
- **No notion of rigor.** A fluent answer and a *correct, grounded* answer look identical
  until you check every source by hand.

### Why Noesis exists

Noesis closes those gaps with three ideas:

1. **Hybrid retrieval over real corpora** — dense vectors + sparse BM25 + three live
   scholarly APIs (arXiv, Semantic Scholar, OpenAlex), fused with Reciprocal Rank Fusion.
2. **Grounded synthesis** — the Writer may only cite papers that are actually in the
   retrieved dossier, with inline `[A1]`, `[S2]`, `[O3]` labels.
3. **Automated peer review** — a Reviewer operator scores the answer on groundedness,
   citation accuracy, coverage, and rigor, and sends weak answers back for revision.

---

## The research workflow

```
Question
   │
   ▼
┌──────────┐   plan (inquiry type, sub-questions, sources)
│ Planner  │
└────┬─────┘
     ▼
┌──────────┐   dense + BM25 + arXiv + Semantic Scholar + OpenAlex
│Retriever │   → fused via Reciprocal Rank Fusion (k=60) → Dossier
└────┬─────┘
     ▼
┌──────────┐   optional sandboxed computation (stats, power analysis)
│ Analyst  │
└────┬─────┘
     ▼
┌──────────┐   streaming, grounded synthesis with inline citations
│  Writer  │
└────┬─────┘
     ▼
┌──────────┐   LLM-as-judge: groundedness · citations · coverage · rigor
│ Reviewer │   ── fail (< 0.5) ──► back to Writer (one retry)
└────┬─────┘
     ▼
  Answer + Dossier + Critic scores + Follow-ups
```

### The workspace system

Research is organised into **workspaces**, each scoping one line of inquiry. A workspace
owns its papers, notes, research questions, experiments, literature reviews, identified
gaps, future ideas, and inquiry history. Domain presets (RA Severity, Patents,
Multimodal AI, VLM) seed a workspace with sensible defaults.

### The inquiry system

An *inquiry* is one question run through the pipeline. Inquiries can run two ways:

- **Synchronous** (`POST /inquiries`) — resolves when the pipeline finishes; good for
  scripting and history replay.
- **Streaming** (`WS /ws/inquiry`) — the UI default. Stage events light up the pipeline
  tracker, answer tokens stream in live, and the dossier and critic scores arrive as
  structured events.

### Retrieval pipeline & dossier generation

The Retriever runs all sources in parallel and fuses their ranked lists with **Reciprocal
Rank Fusion**:

```
score(d) = Σ  1 / (k + rank_i(d))        k = 60
         sources
```

This rewards papers that multiple independent sources agree are relevant, without letting
any single source's score scale dominate. The fused, de-duplicated list is the **dossier** —
the only evidence the Writer is allowed to cite.

### Critic scoring

The Reviewer is an LLM-as-judge that returns four scores in `[0, 1]`:

| Dimension          | Question it answers                                   |
| ------------------ | ----------------------------------------------------- |
| `groundedness`     | Is every claim traceable to a cited source?           |
| `citation_accuracy`| Are the cited sources represented faithfully?         |
| `coverage`         | Is the key literature actually addressed?             |
| `rigor`            | Is the reasoning sound, with no overclaiming?         |

`overall` is a weighted average (groundedness 0.30, citations 0.30, coverage 0.20,
rigor 0.20). Below 0.5 the answer is sent back to the Writer once, with the reviewer's
suggestions injected into the prompt.

---

## Architecture

### System overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend — Next.js 14 (App Router, TS, Tailwind, Zustand, RQ)    │
│  Auth · Workspaces · Inquiry Console · Streaming · Inspector      │
└───────────────┬─────────────────────────────────┬─────────────────┘
       REST (axios)                       WS /ws/inquiry
                │                                 │
┌───────────────▼─────────────────────────────────▼─────────────────┐
│  API Gateway — FastAPI                                            │
│  JWT auth · rate limiting · CORS · request-id · OpenAPI docs      │
└───────────────┬───────────────────────────────────────────────────┘
                │
┌───────────────▼───────────────────────────────────────────────────┐
│  Agent Pipeline — LangGraph StateGraph                            │
│  Planner → Retriever → Analyst → Writer → Reviewer (+ retry edge) │
│  Resilience: circuit breakers · bulkheads · sagas · retries       │
└──────┬───────────────────┬───────────────────────┬────────────────┘
       │                   │                        │
┌──────▼──────┐   ┌────────▼────────┐   ┌───────────▼────────────┐
│ Retrieval   │   │ Data layer      │   │ External scholarly APIs │
│ FastEmbed   │   │ PostgreSQL 16   │   │ arXiv                   │
│ BM25Okapi   │   │ Redis 7         │   │ Semantic Scholar        │
│ RRF (k=60)  │   │ Qdrant (vectors)│   │ OpenAlex                │
│             │   │ MinIO (objects) │   │                         │
└─────────────┘   └─────────────────┘   └─────────────────────────┘
```

### Backend architecture

A FastAPI application with an async SQLAlchemy core. The reasoning pipeline is a compiled
**LangGraph `StateGraph`**: each operator is a node wrapped by a `BaseOperator` that adds a
**bulkhead** (per-operator concurrency cap), a **circuit breaker** (CLOSED → OPEN →
HALF_OPEN), and structured timing. Conditional edges route around the Retriever or Analyst
when the plan doesn't need them, and a conditional edge from the Reviewer creates the
single-retry loop. Celery workers handle background jobs (refresh-token cleanup, BM25 index
rebuilds) on a beat schedule.

### Frontend architecture

Next.js 14 App Router with two route groups: `(auth)` for the signed-out experience and
`(app)` for the authenticated shell. State is split by concern across small Zustand
stores — `auth` (persisted to `localStorage`), `inquiry` (live stream state), `ui`
(command palette / sidebar), and `toast`. Server state (workspaces, history, health) is
owned by TanStack Query. The WebSocket protocol is encapsulated in `useInquirySocket`,
and an axios instance with a single-flight refresh interceptor handles token rotation
transparently.

**Product surfaces.** Beyond the research console, the client ships a full
marketing **landing page** (hero, features, how-it-works, pipeline deep-dive,
evidence showcase, testimonials, pricing, FAQ, CTA), premium **authentication**
with GitHub + Google OAuth entry points, a **document upload** flow with a
drag-and-drop knowledge base, an **agent activity feed** styled after deep-research
tools, **light/dark/system theming** with no-flash hydration, a **command palette**
(⌘K), a **keyboard-shortcuts** overlay (?), and an **onboarding** banner for new users.

```
src/
├── app/
│   ├── page.tsx                        # marketing landing page
│   ├── (auth)/                         # login, register (+ OAuth UI)
│   ├── (app)/                          # authenticated shell + auth guard
│   │   └── workspaces/
│   │       ├── page.tsx                # workspace grid: search, sort, favorites
│   │       └── [workspaceId]/
│   │           ├── page.tsx            # research console + inspector
│   │           └── history/page.tsx    # inquiry history
│   ├── layout.tsx                      # root layout, fonts, no-flash theme script
│   └── providers.tsx                   # React Query + Theme providers
├── components/
│   ├── ui/                             # Button, Input, Dialog, Tabs, Toaster, …
│   ├── layout/                         # Sidebar, Header, CommandPalette, AppShell,
│   │                                   #   ThemeProvider/Toggle, Shortcuts, Onboarding
│   ├── marketing/                      # Hero, Features, Pipeline, Pricing, FAQ, OAuth, …
│   ├── workspace/                      # WorkspaceCard (favorites), WorkspaceDialog
│   ├── library/                        # UploadZone, KnowledgeBase (document upload)
│   └── inquiry/                        # Composer, PipelineTracker, AnswerView,
│                                       #   AgentActivity, Dossier/Critic panels, …
├── hooks/                              # useAuth, useInquirySocket, useHotkey
├── lib/api/                            # axios client + typed endpoint modules + uploads
├── stores/                            # Zustand: auth, inquiry, ui, toast, theme, favorites
├── types/api.ts                        # exact mirrors of backend schemas
└── styles/globals.css                  # light/dark tokens + research prose styles
```

### Database architecture

PostgreSQL 16 (via `asyncpg`) holds 13 tables: `users`, `refresh_tokens`, `workspaces`,
`papers`, `notes`, `research_questions`, `experiments`, `literature_reviews`,
`research_gaps`, `future_ideas`, `timeline_events`, `research_memories`, and `inquiries`.
Schema migrations are managed with Alembic.

### Vector database architecture (Qdrant)

Paper abstracts are embedded with **FastEmbed** (`BAAI/bge-small-en-v1.5`, 384-dim, ONNX)
and stored in **Qdrant**. Dense search is filtered by `workspace_id` so retrieval stays
scoped to the active research line. Qdrant runs as its own service and its collections are
created on application startup.

### Redis architecture

**Redis 7** serves three roles: a rate-limit counter store (`INCR` with TTL, fail-open),
a cache, and the **Celery broker/result backend**.

### Scholarly integrations

- **arXiv** — Atom feed search, no key required.
- **Semantic Scholar** — Graph API; optional `SEMANTIC_SCHOLAR_API_KEY` raises rate limits.
- **OpenAlex** — 250M+ works, fully open; abstracts reconstructed from the inverted index.

### Docker architecture

`docker-compose.yml` brings up the full stack: `postgres`, `redis`, `qdrant`, `minio`,
`backend`, and `frontend`. The frontend ships as a multi-stage build producing a Next.js
**standalone** server image.

---

## Local development

### Prerequisites

- Docker + Docker Compose (recommended), or
- Node.js 20+ and Python 3.12+ for running services individually
- A **Groq API key** (the pipeline's LLM)

### One command (Docker)

```bash
git clone <your-repo-url> noesis && cd noesis
cp .env.example .env          # add GROQ_API_KEY and JWT_SECRET_KEY
docker compose up --build
```

| Service        | URL                              |
| -------------- | -------------------------------- |
| Frontend       | http://localhost:3000            |
| API + docs     | http://localhost:8000/docs       |
| Qdrant         | http://localhost:6333/dashboard  |
| MinIO console  | http://localhost:9001            |

### Frontend only

```bash
cd frontend
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm install
npm run dev                        # http://localhost:3000
```

> **Note:** if `node_modules` was copied from another OS, run a fresh `npm install` on
> your platform (native SWC binaries are platform-specific).

### Frontend scripts

| Script              | Purpose                              |
| ------------------- | ------------------------------------ |
| `npm run dev`       | Dev server with hot reload           |
| `npm run build`     | Production build                     |
| `npm run start`     | Serve the production build           |
| `npm run lint`      | ESLint (next/core-web-vitals)        |
| `npm run typecheck` | `tsc --noEmit`, strict mode          |

---

## Environment variables

### Frontend

| Variable                   | Default                  | Description            |
| -------------------------- | ------------------------ | ---------------------- |
| `NEXT_PUBLIC_API_BASE_URL`   | `http://localhost:8000` | Base URL of the API                       |
| `NEXT_PUBLIC_GITHUB_OAUTH_URL`| *(derived)*            | GitHub OAuth initiator URL                |
| `NEXT_PUBLIC_GOOGLE_OAUTH_URL`| *(empty)*              | Google OAuth URL; empty disables the button |

### Backend (reference)

| Variable                     | Required | Description                          |
| ---------------------------- | -------- | ------------------------------------ |
| `GROQ_API_KEY`               | yes      | LLM provider key                     |
| `JWT_SECRET_KEY`             | yes      | Signing key for access/refresh JWTs  |
| `DATABASE_URL`               | yes      | Async PostgreSQL DSN                 |
| `REDIS_URL`                  | yes      | Redis connection URL                 |
| `QDRANT_URL`                 | yes      | Qdrant endpoint                      |
| `SEMANTIC_SCHOLAR_API_KEY`   | no       | Higher Semantic Scholar rate limits  |
| `GITHUB_CLIENT_ID` / `_SECRET` | no     | Enables GitHub OAuth                 |

---

## Production deployment

The backend builds into a standard Python image and scales horizontally behind a load
balancer (JWTs are stateless; refresh tokens live in Postgres). The frontend's standalone
output deploys to any Node host or container platform — set `NEXT_PUBLIC_API_BASE_URL` to
your public API origin at build time. Postgres, Redis, Qdrant, and MinIO are expected as
managed or containerised dependencies. Point Celery workers at the same Redis broker.

---

## API overview

Base path: `/api/v1`

### Auth

| Method | Path             | Body                                   |
| ------ | ---------------- | -------------------------------------- |
| POST   | `/auth/register` | `{ username, email, password }` (JSON) |
| POST   | `/auth/login`    | `username`, `password` (form-encoded)  |
| POST   | `/auth/refresh`  | `{ refresh_token }`                    |
| POST   | `/auth/logout`   | `{ refresh_token }`                    |
| GET    | `/auth/me`       | — (Bearer token)                       |
| GET    | `/auth/me/stats` | — (Bearer token)                       |

### Workspaces

| Method | Path                              |
| ------ | --------------------------------- |
| GET    | `/workspaces`                     |
| POST   | `/workspaces`                     |
| GET    | `/workspaces/presets`             |
| POST   | `/workspaces/from-preset/{key}`   |
| GET    | `/workspaces/{id}`                |
| PATCH  | `/workspaces/{id}`                |
| DELETE | `/workspaces/{id}`                |
| GET    | `/workspaces/{id}/stats`          |

### Inquiries

| Method | Path                | Notes                          |
| ------ | ------------------- | ------------------------------ |
| POST   | `/inquiries`        | Synchronous run                |
| GET    | `/inquiries`        | History (`?workspace_id&limit`)|
| GET    | `/inquiries/{id}`   | Full detail                    |

### Library

| Method | Path                                          |
| ------ | --------------------------------------------- |
| GET/POST   | `/workspaces/{id}/library/papers`         |
| DELETE     | `/workspaces/{id}/library/papers/{paper}` |
| GET/POST   | `/workspaces/{id}/library/notes`          |

## WebSocket overview

`WS /api/v1/ws/inquiry?token=<JWT>&workspace_id=<id>`

The client sends `{ "question": "…" }`. The server streams:

| Event                                   | Meaning                          |
| --------------------------------------- | -------------------------------- |
| `{ type: "stage", stage }`              | Pipeline stage transition        |
| `{ type: "token", content }`            | One chunk of the streamed answer |
| `{ type: "dossier", items }`            | The retrieved evidence list      |
| `{ type: "critic", scores }`            | Peer-review scores               |
| `{ type: "done", inquiry_id }`          | Completion                       |
| `{ type: "error", message }`            | Failure                          |

---

## Roadmap

- **Library ingestion UI** — upload PDFs, auto-embed into the workspace corpus.
- **Experiment planner surface** — turn `experiment_design` inquiries into tracked plans.
- **Research timeline** — chronological view of inquiries, gaps, and ideas per workspace.
- **Collaborative workspaces** — shared workspaces with roles and comments.
- **Citation graph** — visualise how dossier papers cite one another.
- **Export** — one-click export of an inquiry to Markdown / LaTeX / BibTeX.

---

## Tech stack

**Frontend** — Next.js 14, TypeScript (strict), Tailwind CSS, Zustand, TanStack Query,
Axios, Framer Motion, Lucide, cmdk.
**Backend** — FastAPI, LangGraph, async SQLAlchemy, Pydantic, Celery.
**Data** — PostgreSQL 16, Redis 7, Qdrant, MinIO.
**Retrieval** — FastEmbed (BGE-small ONNX), BM25Okapi, arXiv, Semantic Scholar, OpenAlex.

---

<div align="center">
<sub>Built for researchers who want answers they can cite.</sub>
</div>
