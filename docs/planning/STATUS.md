# Status

- **Last run:** 2026-10-21 (run 13, admin studio seasons)
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

Sprint 1: auth module, `require_role`, auth tests, rate limiting, login lockout and profiles CRUD, catalog models and public catalog endpoints done; admin catalog CRUD, audit log and seed script done (all Sprint 1 backend tasks complete); frontend auth pages, token handling and the profile picker/management done; browse, title detail and the admin studio done; the admin studio is complete (titles, publishing, seasons, episodes, reorder). Left in Sprint 1: the E2E test, a real-browser performance/contrast check, and the retro. Full list: docs/planning/github-issues.md.

## Decisions made

- D1: License = Apache-2.0 (ADR-0009, accepted).
- D9: Maturity scale all < 7+ < 13+ < 16+ < 18+ (ADR-0012); customer to confirm.
- D10: Catalog visibility rule, default anonymous limit `13+`, keyset pagination (ADR-0013).
- D11: Frontend stack pins: ESLint 9, TypeScript 5.9, `@hookform/resolvers` 5 (v6 has a peer conflict), MSW 3 (`onUnhandledFrame`). Revisit when upstream catches up.
- D8: Cloudinary only for development and a tiny invite-only pilot; usage guard thresholds configurable, fails safe, no guarantee against charges (ADR-0011). Paid worker host and any paid plan need an approved budget; none selected.
- D7: Video = Cloudinary Free (ADR-0011), replacing Mux for the pilot.
- D4: Hosting = Render + Neon + owner-managed Redis (ADR-0010, accepted).
- D2: Frontend pinned to ESLint 9 and TypeScript 5.9 because `eslint-plugin-jsx-a11y` and `openapi-typescript` do not yet support ESLint 10 / TypeScript 6+. Revisit when they do.
- D3: GitHub labels, milestones (Sprints 0 to 6) and 31 issues (Sprints 0 and 1) were created on GitHub; docs/planning/github-issues.md mirrors them.

## Open questions (answerable in one line)

0. Q12: Sessions need the frontend and API on the same site. Approve a custom domain for the pilot (needs customer approval, Q9), or should I test a same-origin proxy on the free hosts first? See docs/frontend/auth-and-api-client.md.

1. Q9: Cloudinary Free allows roughly 3 hours of total SD viewing per month (ADR-0011). Keep the pilot invite-only and tiny, or ask the customer to fund a plan before public launch?
2. Q10: Please confirm the Free plan's max upload size and streaming terms on your Cloudinary dashboard once the account exists (I could not verify them).
3. Q11: Create a Cloudinary account and give me credentials as environment variables only (never in chat).

Resolved 2026-10-21: license (ADR-0009), hosting (ADR-0010), video provider = Cloudinary Free (ADR-0011), ARQ worker, customer confirmation process (below).

## Decisions on workers and customer sign-off

- D5: ARQ worker runs locally with Redis during development and testing, as a separate process from FastAPI. Before the public pilot, choose a worker-capable host and confirm its cost (no free Render worker). Not decided yet: the host.
- D6: The recorded customer answers stay proposed defaults. Explicit customer approval is required before public launch for: content distribution rights, expected pilot traffic, and the post-pilot infrastructure budget. Tracked as a launch gate in Sprint 6.

## Remaining for Phase 1 (closed with one caveat)

- Caveat: `docker compose up -d` and `make backend-dev` end to end were not run in the authoring sandbox (no Docker). CI builds both images and runs the backend against live Postgres and Redis. Owner to run compose once locally.

## Next action

Merge the seasons PR when CI is green. All Sprint 1 build tasks are then done. Remaining for Sprint 1: the end-to-end test and a real-browser check of LCP and colour contrast (both need a browser, which this sandbox does not have), then the retro and the Sprint 2 plan (Cloudinary provider, upload, usage guard). Sprint 2 can start without the browser checks. No paid infrastructure is needed; Q12 (same-site cookies), Q9 (Cloudinary capacity) and the customer confirmations must be answered before the pilot.
