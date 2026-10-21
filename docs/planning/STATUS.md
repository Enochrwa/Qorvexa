# Status

- **Last run:** 2026-10-21 (run 1, Phase 1)
- **Current sprint:** Sprint 0, Foundation (2026-10-21 to 2026-11-03)
- **Phase 1:** in progress (not done: see "Remaining for Phase 1")
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
| Protect `main`, secret scanning, Dependabot | blocked: config files added; applying repo settings needs owner approval (see docs/devops/ci-cd.md) |
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
| Confirm customer inputs | blocked: needs customer (see questions) |
| Finalize ADR-0003 | blocked: depends on customer inputs |
| Free-tier research | done (docs/research/free-tier-findings.md) |

Sprint 1 tasks: see docs/planning/github-issues.md (all todo).

## Decisions made

- D1: License = Apache-2.0 (ADR-0009, proposed; change before first release if the customer needs ownership).
- D2: Frontend pinned to ESLint 9 and TypeScript 5.9 because `eslint-plugin-jsx-a11y` and `openapi-typescript` do not yet support ESLint 10 / TypeScript 6+. Revisit when they do.
- D3: GitHub labels, milestones (Sprints 0 to 6) and 31 issues (Sprints 0 and 1) were created on GitHub; docs/planning/github-issues.md mirrors them.

## Open questions (answerable in one line)

1. Q1: Approve applying the `main` branch protection settings from docs/devops/ci-cd.md?
2. Q2: Confirm Apache-2.0, or choose another license?
3. Q3: ARQ would exceed Upstash's free 500K commands per month. Run Redis only locally/CI for now and decide queue strategy before Sprint 2?
4. Q4: Customer inputs 1 to 10 in docs/planning/risks-and-open-questions.md are still unanswered.
5. Q5: Which free host for the API (Render free sleeps after 15 min, no free worker) and Postgres (Neon free 0.5 GB)? Approve as the pilot candidates?

## Remaining for Phase 1

- Apply branch protection after approval (Q1).
- Verify `docker compose up -d` and `make backend-dev` end to end on a machine with Docker (compose was not run in the authoring sandbox).
- Customer inputs and ADR-0003 finalization (blocked).

## Next action

Get answers to Q1 to Q5, apply branch protection, run compose once locally, then mark Phase 1 done and start Sprint 1 with the auth module.
