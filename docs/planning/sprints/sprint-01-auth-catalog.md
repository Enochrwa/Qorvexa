# Sprint 1: Accounts and catalog

**Goal:** users can sign up, manage profiles and browse a seeded catalog; admins can manage metadata.
**Requirements:** FR-A1, FR-A2, FR-A3, FR-C1, FR-S3 (metadata part), FR-S5, FR-C4 (basic)
**Dates:** 2026-11-04 to 2026-11-17

## Tasks

### Backend
- [x] Auth module: register, verify email, login, refresh rotation, logout, reset ([auth.md](../../backend/auth.md)) (L) (rate limits and lockout done in the rate-limiting task)
- [x] Roles and dependencies (`require_role`) (S)
- [x] Profiles CRUD with maturity limit and prefs (M) (default profile at registration; `X-Profile-Id` dependency added for profile-scoped endpoints)
- [x] Catalog models and migrations: titles, seasons, episodes, genres, people (L)
- [x] Public catalog endpoints: list, detail, seasons, genres, filters, cursor pagination (L) (ADR-0013; list p95 under 20 ms on 5,000 seeded titles, local Postgres)
- [x] Admin catalog CRUD endpoints with validation (L) (titles, seasons, episodes, reorder, publish/unpublish, audit log; poster/subtitle editing waits for media in Sprint 2)
- [x] Seed script (admin user, genres, sample titles) (M) (`make seed`; admin only from SEED_ADMIN_* env vars)
- [x] Rate limiting on auth endpoints (S) (plus login lockout)

### Frontend
- [x] Auth pages (login, register, verify, forgot/reset) with forms and validation (L)
- [x] Token handling: in-memory access token, refresh single-flight (M)
- [x] Profile picker and management (M)
- [ ] Browse page with filters, skeletons, responsive grid (L)
- [ ] Title detail page: hero, synopsis, seasons/episodes list (L)
- [x] Admin studio shell: role-guarded route, titles list, title editor, publish/unpublish/delete (M)
- [x] Admin studio: seasons and episodes editor with reorder (M) (keyboard reorder via Up/Down buttons, announced to screen readers)

### Quality
- [x] Unit/integration tests per [backend testing](../../backend/testing.md) for auth and authorization (M)
- [ ] E2E: register -> create profile -> browse -> open title (M)

## Acceptance criteria

- Refresh token reuse is detected and revokes the family (test).
- Editor cannot access admin-only endpoints (test).
- Browse page LCP under 2.5 s on throttled 4G with seeded data.
- Migration upgrade and downgrade both work in CI.

## Log

- 2026-10-22: Seasons and episodes editor with reorder on branch `feat/frontend-admin-seasons` (205 frontend tests; verified against the real backend). Remaining Sprint 1: E2E, real-browser LCP/contrast check, retro.

- 2026-10-22: Admin studio (guard, titles list, title editor, publishing) on branch `feat/frontend-admin-titles` (183 frontend tests; verified against the real backend including the audit trail). Studio routes are lazy-loaded. Remaining: seasons/episodes editor, E2E, real-browser LCP/contrast check, retro.

- 2026-10-22: Browse and title detail pages on branch `feat/frontend-catalog` (149 frontend tests; verified against the real backend with 61 titles across 3 cursor pages). Declared catalog response schemas so the frontend is typed. Remaining: admin studio shell, E2E, perf check (LCP) in a real browser, retro.

- 2026-10-22: Profile picker and management on branch `feat/frontend-profiles` (88 frontend tests). Verified against the real backend that the selected profile changes catalog results. Remaining frontend: browse page, title detail, admin studio shell, E2E.

- 2026-10-22: Frontend auth pages and token handling on branch `feat/frontend-auth` (typed API client, 63 frontend tests, axe clean). Found and fixed a backend CORS bug (custom headers rejected on preflight) that mocked tests could not see; verified the client against the real backend.

- 2026-10-22: Admin catalog CRUD, audit log (migration 0005) and seed script on branch `feat/admin-catalog`. 136 backend tests green. All Sprint 1 backend tasks are done; frontend tasks remain.

- 2026-10-22: Catalog models, migration 0004 and public catalog endpoints on branch `feat/catalog`. Admin CRUD, seed script and frontend tasks remain.

- 2026-10-21: Profiles CRUD, default profile at registration, `require_profile` dependency, maturity scale (ADR-0012) on branch `feat/profiles`. 83 backend tests green with real Postgres and Redis.

- 2026-10-21: Rate limiting and login lockout on branch `feat/auth-rate-limiting` (Redis, in-process fallback). 56 backend tests green with real Postgres and Redis.

- 2026-10-21: Auth module, `require_role` and tests on branch `feat/auth-and-roles`. 40 backend tests green against real Postgres (auth modules 96 to 100% line coverage). Rate limiting and login lockout not done yet.

-

## Retro

-
