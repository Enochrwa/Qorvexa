# Status

- **Last run:** 2026-10-21 (run 2, decisions recorded)
- **Current sprint:** Sprint 0, Foundation (2026-10-21 to 2026-11-03)
- **Phase 1:** done 2026-10-21 (one caveat below)
- **Branch:** `chore/phase-1-foundation`

## Sprint calendar

| Sprint | Dates | Theme |
|---|---|---|
| 0 | 2026-10-21 to 2026-11-03 | Foundation |
| 1 | 2026-11-04 to 2026-11-17 | Accounts and catalog |
| 2 | 2026-11-18 to 2026-12-01 | Upload and processing |
| 3 | 2026-12-02 to 2026-12-15 | Player and playback |
| 4 | 2026-12-16 to 2026-12-29 | Discovery and engagement |
| 5 | 2026-12-30 to 2027-01-12 | Downloads, performance, security |
| 6 | 2027-01-13 to 2027-01-26 | Pilot readiness |

## Sprint 0 tasks

| Task | State |
|---|---|
| Protect `main`, secret scanning, Dependabot | done (see run notes; settings per docs/devops/ci-cd.md) |
| Backend scaffold | done (local checks green) |
| Frontend scaffold | done (local checks green) |
| Dockerfiles | done; both images build in CI (`docker` job green on PR #32) |
| `docker compose` and Makefile targets verified | in progress: Makefile targets run for backend and frontend; compose not run |
| CI green on an empty PR | done: backend (live Postgres + Redis, migration applied), frontend, docker, docs all green on PR #32 |
| Async session, Alembic initial migration | done; applied to live Postgres in CI |
| Problem+JSON, request ID, logging | done |
| Config via env, `.env.example` | done |
| App shell, router, error boundary, query provider | done |
| Design tokens, Button, Input, Skeleton | done |
| OpenAPI client generation script | done (verified against an exported schema) |
| Confirm customer inputs | done: answers recorded; customer confirmation pending (Q8) |
| Finalize ADR-0003 | done for the abstraction; Mux spend pending Q6 |
| Free-tier research | done (docs/research/free-tier-findings.md) |

Sprint 1 tasks: see docs/planning/github-issues.md (all todo).

## Decisions made

- D1: License = Apache-2.0 (ADR-0009, accepted).
- D4: Hosting = Render + Neon + owner-managed Redis (ADR-0010, accepted).
- D2: Frontend pinned to ESLint 9 and TypeScript 5.9 because `eslint-plugin-jsx-a11y` and `openapi-typescript` do not yet support ESLint 10 / TypeScript 6+. Revisit when they do.
- D3: GitHub labels, milestones (Sprints 0 to 6) and 31 issues (Sprints 0 and 1) were created on GitHub; docs/planning/github-issues.md mirrors them.

## Open questions (answerable in one line)

1. Q6: Approve Mux storage spend (about $1.80 per month per 10 hours of video) for the pilot, or stay on LocalProvider (MinIO + FFmpeg)? ADR-0003.
2. Q7: Where will the ARQ worker run for the pilot (Render has no free worker; Redis is yours)?
3. Q8: The customer still has to confirm the recorded answers, especially content rights and post-pilot budget.

Resolved 2026-10-21: license Apache-2.0 (ADR-0009), Render + Neon + owner-managed Redis (ADR-0010), branch protection approved, customer answers recorded in risks-and-open-questions.md.

## Remaining for Phase 1 (closed with one caveat)

- Caveat: `docker compose up -d` and `make backend-dev` end to end were not run in the authoring sandbox (no Docker). CI builds both images and runs the backend against live Postgres and Redis. Owner to run compose once locally.

## Next action

Sprint 1, first slice: auth module (register, login, refresh rotation with reuse detection) plus `require_role`, with tests. Blocked items: Q6, Q7, Q8 do not block Sprint 1.
