# Qorvexa

A web-based video-on-demand platform for movies and drama series: adaptive-bitrate streaming, an advanced player, downloads, personalized discovery and an admin studio for content upload and management.

> **Status:** Foundation (Sprint 0). Backend and frontend scaffolds exist; no product features yet. See [docs/planning/STATUS.md](docs/planning/STATUS.md). See [docs/planning/roadmap.md](docs/planning/roadmap.md).

## Product goals

- Fast, reliable playback on any connection (HLS adaptive bitrate).
- A premium player: quality, speed, captions, audio tracks, PiP, keyboard shortcuts, resume, next episode.
- Discovery that keeps viewers coming back: profiles, watchlist, continue watching, recommendations, mood collections.
- A real admin studio: resumable uploads, processing status, metadata editing, scheduling, analytics.
- Built on a **$0 budget** for the prototype, with an honest cost model for launch ([docs/architecture/infrastructure-and-costs.md](docs/architecture/infrastructure-and-costs.md)).

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React + TypeScript + Vite, Tailwind CSS, TanStack Query, Zustand, React Router |
| Player | hls.js (default) with Shaka Player evaluated for offline; custom controls |
| Backend | Python, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Database | PostgreSQL (primary), Redis (cache, rate limits, job queue) |
| Jobs | ARQ (Redis) workers |
| Video | Provider abstraction: Mux (pilot) or Cloudflare R2 + FFmpeg (self-managed) |
| Hosting (free-tier) | Cloudflare Pages (static frontend), free-tier API and Postgres hosts (verify limits) |
| Quality | Ruff, mypy, pytest, ESLint, Prettier, Vitest, Playwright, GitHub Actions |

Rationale for each choice: [docs/adr](docs/adr/README.md).

## Repository layout

```
Qorvexa/
├── backend/            FastAPI application (see backend/README.md)
├── frontend/           React + TypeScript application (see frontend/README.md)
├── infra/              Docker, deployment and environment config
├── scripts/            Developer helper scripts
├── docs/               All planning, architecture and development documentation
│   ├── product/        Vision, requirements, personas, UX
│   ├── architecture/   System design, video pipeline, costs
│   ├── adr/            Architecture decision records
│   ├── backend/        Backend guides
│   ├── frontend/       Frontend guides and player spec
│   ├── database/       Schema and migrations
│   ├── api/            API design and endpoint catalog
│   ├── devops/         Environments, CI/CD, deployment, monitoring
│   ├── security/       Security and legal/compliance
│   ├── planning/       Roadmap, sprints, backlog, risks
│   ├── ideas/          Ideas and future features
│   └── research/       Research notes and verified findings
└── .github/            CI workflows and templates
```

Start at the [documentation index](docs/README.md).

## Quick start (target workflow)

```bash
cp .env.example .env
make install                # backend (uv) and frontend (npm) dependencies
docker compose up -d        # Postgres, Redis, MinIO, Mailpit
make migrate                # apply Alembic migrations
make seed                   # genres + sample titles; admin only if SEED_ADMIN_EMAIL/SEED_ADMIN_PASSWORD are set
make backend-dev            # FastAPI on :8000
make frontend-dev           # Vite on :5173
```

The backend and frontend run today; compose and Docker images are verified in CI. Sprint 0 status: see [docs/planning/sprints/sprint-00-foundation.md](docs/planning/sprints/sprint-00-foundation.md).

## Content and legal

Only content the customer owns or is licensed to distribute may be uploaded. See [docs/security/legal-compliance.md](docs/security/legal-compliance.md).
