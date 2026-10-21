# Backend testing

## Pyramid

| Level | Scope | Tools |
|---|---|---|
| Unit | Pure logic: recommendation scoring, state machine, token handling | pytest |
| Integration | Router + service + real Postgres (and Redis) | pytest-asyncio, httpx `AsyncClient`, CI service containers |
| Contract | Provider webhooks and signatures | Recorded payload fixtures |
| End-to-end | Critical flows through the UI | Playwright (see frontend/testing.md) |
| Load | Catalog, search, playback sessions | k6 |

## Conventions

- Each test runs in a transaction rolled back after the test, or uses a fresh schema.
- Factories (factory-boy) for models; no shared mutable fixtures.
- Freeze time for token expiry and scheduling tests.
- Mock only the outside world (providers, email), not the database.
- Coverage target: 80% lines overall, 90% for `auth`, `media` state machine and `playback`.

## Must-have tests before the pilot

- Auth: register, verify, login, refresh rotation, reuse detection, lockout, role enforcement.
- Authorization: profile ownership, maturity limit, unpublished title access, editor vs admin.
- Media: upload session creation, webhook idempotency, state transitions, reconciliation.
- Playback: progress upsert, resume, next-episode selection.
- Search: ranking sanity and typo tolerance.
- Recommendations: excludes finished and over-maturity titles; diversity rule.

## Running

```bash
cd backend
uv run pytest -q
uv run pytest --cov=app --cov-report=term-missing
```
