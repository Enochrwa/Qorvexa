# Sprint 0: Foundation

**Goal:** a working dev environment, CI green, and the skeleton both apps build on.
**Dates:** 2026-10-21 to 2026-11-03

## Scope and tasks

### Repo and tooling
- [ ] Protect `main`, enable Dependabot and secret scanning (S) (Dependabot config and plan done; applying settings needs owner approval)
- [x] Backend scaffold: `uv`, FastAPI app factory, settings, `/health` and `/ready`, Ruff, mypy, pytest (M)
- [x] Frontend scaffold: Vite + React + TS strict, Tailwind, ESLint, Prettier, Vitest (M)
- [ ] `docker compose` services verified; `Makefile` targets work (S)
- [ ] CI passes on an empty PR for backend and frontend (S)
- [x] Backend and frontend Dockerfiles (non-root, multi-stage) (M)

### Backend foundations
- [x] Async SQLAlchemy session, Alembic initial migration (extensions, `users`) (M)
- [x] Problem+JSON error handler, request ID middleware, structured logging (M)
- [x] Config via env; `.env.example` complete (S)

### Frontend foundations
- [x] App shell, router, error boundary, query client provider (M)
- [x] Design tokens and first primitives: Button, Input, Skeleton (M)
- [x] OpenAPI client generation script (S)

### Decisions
- [ ] Confirm customer inputs (see [risks](../risks-and-open-questions.md)) (S)
- [ ] Finalize ADR-0003 status after content-volume answers (S)
- [x] Record chosen free-tier hosts and verified limits in [research notes](../../research/free-tier-findings.md) (M)

## Acceptance criteria

- `docker compose up -d && make backend-dev` serves `/health` = 200.
- `make frontend-dev` shows the app shell.
- CI is green on `main`.
- A new developer can run the project from the README in under 15 minutes.

## Risks

Free-tier host limits discovered late; mitigate by verifying before Sprint 5.

## Log

- 2026-10-21: Phase 1 on branch `chore/phase-1-foundation`. Backend (4 tests, ruff, mypy strict) and frontend (5 tests, lint, typecheck, build) green locally. Docker images and compose not run locally (no Docker in the sandbox); CI builds them. Initial migration verified as offline SQL only, not against a live Postgres. Free-tier limits verified; see research notes.

## Retro

-
