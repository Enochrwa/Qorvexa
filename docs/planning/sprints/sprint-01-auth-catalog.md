# Sprint 1: Accounts and catalog

**Goal:** users can sign up, manage profiles and browse a seeded catalog; admins can manage metadata.
**Requirements:** FR-A1, FR-A2, FR-A3, FR-C1, FR-S3 (metadata part), FR-S5, FR-C4 (basic)
**Dates:** 2026-11-04 to 2026-11-17

## Tasks

### Backend
- [x] Auth module: register, verify email, login, refresh rotation, logout, reset ([auth.md](../../backend/auth.md)) (L) (rate limits and lockout done in the rate-limiting task)
- [x] Roles and dependencies (`require_role`) (S)
- [ ] Profiles CRUD with maturity limit and prefs (M)
- [ ] Catalog models and migrations: titles, seasons, episodes, genres, people (L)
- [ ] Public catalog endpoints: list, detail, seasons, genres, filters, cursor pagination (L)
- [ ] Admin catalog CRUD endpoints with validation (L)
- [ ] Seed script (admin user, genres, sample titles) (M)
- [x] Rate limiting on auth endpoints (S) (plus login lockout)

### Frontend
- [ ] Auth pages (login, register, verify, forgot/reset) with forms and validation (L)
- [ ] Token handling: in-memory access token, refresh single-flight (M)
- [ ] Profile picker and management (M)
- [ ] Browse page with filters, skeletons, responsive grid (L)
- [ ] Title detail page: hero, synopsis, seasons/episodes list (L)
- [ ] Admin studio shell and title/season/episode editor (L)

### Quality
- [x] Unit/integration tests per [backend testing](../../backend/testing.md) for auth and authorization (M)
- [ ] E2E: register -> create profile -> browse -> open title (M)

## Acceptance criteria

- Refresh token reuse is detected and revokes the family (test).
- Editor cannot access admin-only endpoints (test).
- Browse page LCP under 2.5 s on throttled 4G with seeded data.
- Migration upgrade and downgrade both work in CI.

## Log

- 2026-10-21: Rate limiting and login lockout on branch `feat/auth-rate-limiting` (Redis, in-process fallback). 56 backend tests green with real Postgres and Redis.

- 2026-10-21: Auth module, `require_role` and tests on branch `feat/auth-and-roles`. 40 backend tests green against real Postgres (auth modules 96 to 100% line coverage). Rate limiting and login lockout not done yet.

-

## Retro

-
