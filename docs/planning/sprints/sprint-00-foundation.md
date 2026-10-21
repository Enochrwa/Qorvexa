# Sprint 0: Foundation

**Goal:** a working dev environment, CI green, and the skeleton both apps build on.
**Dates:** TBD

## Scope and tasks

### Repo and tooling
- [ ] Protect `main`, enable Dependabot and secret scanning (S)
- [ ] Backend scaffold: `uv`, FastAPI app factory, settings, `/health` and `/ready`, Ruff, mypy, pytest (M)
- [ ] Frontend scaffold: Vite + React + TS strict, Tailwind, ESLint, Prettier, Vitest (M)
- [ ] `docker compose` services verified; `Makefile` targets work (S)
- [ ] CI passes on an empty PR for backend and frontend (S)
- [ ] Backend and frontend Dockerfiles (non-root, multi-stage) (M)

### Backend foundations
- [ ] Async SQLAlchemy session, Alembic initial migration (extensions, `users`) (M)
- [ ] Problem+JSON error handler, request ID middleware, structured logging (M)
- [ ] Config via env; `.env.example` complete (S)

### Frontend foundations
- [ ] App shell, router, error boundary, query client provider (M)
- [ ] Design tokens and first primitives: Button, Input, Skeleton (M)
- [ ] OpenAPI client generation script (S)

### Decisions
- [ ] Confirm customer inputs (see [risks](../risks-and-open-questions.md)) (S)
- [ ] Finalize ADR-0003 status after content-volume answers (S)
- [ ] Record chosen free-tier hosts and verified limits in [research notes](../../research/free-tier-findings.md) (M)

## Acceptance criteria

- `docker compose up -d && make backend-dev` serves `/health` = 200.
- `make frontend-dev` shows the app shell.
- CI is green on `main`.
- A new developer can run the project from the README in under 15 minutes.

## Risks

Free-tier host limits discovered late; mitigate by verifying before Sprint 5.

## Log

-

## Retro

-
