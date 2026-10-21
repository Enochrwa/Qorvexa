# Backend guide

Python 3.12+, FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, asyncpg, Redis, ARQ.

## Tooling

| Purpose | Tool |
|---|---|
| Env and deps | `uv` (pyproject.toml, lockfile) |
| Lint/format | Ruff |
| Types | mypy (strict on `app/`) |
| Tests | pytest, pytest-asyncio, httpx, factory-boy, testcontainers or CI Postgres |
| Migrations | Alembic |
| Logging | structlog (JSON in prod) |
| Errors | Sentry SDK (optional) |

## Project structure

```
backend/
├── pyproject.toml
├── alembic.ini
├── alembic/
│   └── versions/
├── app/
│   ├── main.py                 App factory, middleware, router mounting
│   ├── core/
│   │   ├── config.py           Pydantic Settings (env)
│   │   ├── db.py               Async engine and session
│   │   ├── security.py         Hashing, JWT, tokens
│   │   ├── deps.py             Shared FastAPI dependencies
│   │   ├── errors.py           Problem+JSON error handlers
│   │   ├── logging.py
│   │   └── rate_limit.py
│   ├── modules/
│   │   ├── auth/               router.py, schemas.py, service.py, models.py, repo.py
│   │   ├── profiles/
│   │   ├── catalog/
│   │   ├── media/              Provider interface and implementations live in providers/
│   │   │   └── providers/      base.py, local.py, mux.py, r2_ffmpeg.py
│   │   ├── playback/
│   │   ├── engagement/
│   │   ├── search/
│   │   └── admin/
│   ├── workers/
│   │   ├── settings.py         ARQ WorkerSettings
│   │   └── jobs/               reconcile_assets.py, publish_scheduled.py, recommendations.py, notifications.py
│   └── api/
│       └── v1/router.py        Aggregates module routers
└── tests/
    ├── unit/
    ├── integration/
    └── conftest.py
```

### Module layering

`router` (HTTP, validation) -> `service` (business rules, transactions) -> `repo` (queries). Routers never touch the session directly; services never import FastAPI. Modules interact through service functions, not each other's models.

## Conventions

- Async everywhere; no blocking calls in request handlers (use thread pool or worker).
- Schemas separate from ORM models (`XCreate`, `XUpdate`, `XRead`).
- IDs are UUIDv7 (time-ordered) or UUID4; public slugs for titles.
- UTC timestamps (`timestamptz`).
- All list endpoints use cursor pagination.
- Errors follow RFC 9457 Problem Details.
- Config only via environment; no secrets in code.

## Running locally

```bash
docker compose up -d
cd backend && uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run arq app.workers.settings.WorkerSettings   # separate terminal
```

OpenAPI is served at `/docs` and `/openapi.json`; the frontend generates its typed client from the latter.
