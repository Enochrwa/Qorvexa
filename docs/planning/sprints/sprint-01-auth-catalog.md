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
- [x] Browse page with filters, skeletons, responsive grid (L)
- [x] Title detail page: hero, synopsis, seasons/episodes list (L)
- [x] Admin studio shell: role-guarded route, titles list, title editor, publish/unpublish/delete (M)
- [x] Admin studio: seasons and episodes editor with reorder (M) (keyboard reorder via Up/Down buttons, announced to screen readers)

### Quality
- [x] Unit/integration tests per [backend testing](../../backend/testing.md) for auth and authorization (M)
- [x] E2E: register -> create profile -> browse -> open title (M) (Playwright, real Chromium, desktop and phone; docs/devops/e2e.md)

## Acceptance criteria

- Refresh token reuse is detected and revokes the family (test). **Met** (backend test; also exercised against the real API).
- Editor cannot access admin-only endpoints (test). **Met** (a sweep test over every admin operation; viewers get 403).
- Browse page LCP under 2.5 s on throttled 4G with seeded data. **Met with a small margin**: median 1.96 s cold cache (Slow 4G, 4x CPU, phone viewport, 200 titles, zero layout shift). Not measured: real poster images, real hosting. See docs/research/browser-measurements.md.
- Migration upgrade and downgrade both work in CI. **Met** (CI runs up, down, up on Postgres).

## Log

- 2026-10-23: Found by the first CI run of the browser tests and fixed: a lost or aborted refresh response signed users out (refresh grace, ADR-0014, plus one client retry). The old 'two tabs' known gap is closed.
- 2026-10-23: Sprint 1 closed. E2E suite and real-browser checks added (23 browser tests); fixed colour contrast; measured LCP; verified the cross-site cookie problem. Retro below.
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

## Retro

_Sprint 1 ran 2026-10-21 to 2026-10-23 (the plan allowed until 2026-11-17)._

**Delivered:** auth with rotating refresh tokens and reuse detection, roles, rate limiting and lockout, profiles with maturity limits, catalog with one visibility rule, admin CRUD with audit log, seed script, and the whole frontend (auth, profiles, browse, detail, admin studio incl. keyboard reorder). 146 backend tests, 215 frontend unit tests, 23 browser tests (desktop and phone). Zero paid services.

**What worked**
- Running the real client against the real backend after each slice (and later a real browser) found bugs that mocked tests could not: CORS preflight rejecting our own custom headers, catalog responses typed `unknown`, colour contrast below WCAG AA, cookies refused across sites.
- Mutation checks (temporarily break the logic, see the test fail) caught tests that passed for the wrong reason, including a contrast guard that was silently reading an empty file.
- Small, reviewable PRs through protected `main`, each with its CI green before merge.

**What did not**
- I committed local artifacts twice (a Redis dump, TypeScript build caches). Harmless here (no secrets, checked) but avoidable; CI now blocks those file types.
- Several tests were wrong, not the app (rounding, locators). Cheap, but it cost iterations; prefer role-and-name locators and exact matches.
- Real-browser checks came last. They should have come earlier: the contrast and cookie findings would have been cheaper in Sprint 1's first week.

**Found late, by real-browser CI:** a token-rotation race (lost refresh response, quick reload) could sign users out. The mocked and local tests could not see it because localhost answers instantly. Fixed (ADR-0014).

**Changes for Sprint 2**
1. Run the e2e suite in CI on every PR (job added, informational until proven stable, then required).
2. Check the real browser on each UI slice, not at the end.
3. Decide the same-site hosting question (Q12) before building anything deploy-specific.
4. Keep the `VideoProvider` abstraction honest with a contract test that every provider must pass.
