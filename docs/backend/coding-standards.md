# Backend coding standards

## Style

- Ruff for lint and format (line length 100). Rules: `E,F,I,B,UP,S,ASYNC,SIM,RUF`.
- Type hints everywhere; mypy strict for `app/`. No `Any` without a comment.
- Names: modules `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`.
- Docstrings on public services and non-obvious functions (what and why, not how).

## Patterns

- Dependency injection through FastAPI `Depends`; keep dependencies small and testable.
- Transactions are owned by services (`async with session.begin()`), one unit of work per request.
- Do not return ORM objects from routers; map to Pydantic schemas.
- Raise domain exceptions in services (`NotFound`, `Conflict`, `Forbidden`); translate in the error handler.
- Idempotency for webhooks and jobs: use unique event IDs and upserts.
- No business logic in routers; no HTTP concerns in services.

## Database

- Explicit loading strategy (`selectinload`/`joinedload`); avoid N+1.
- Every query on a large table must use an index (check with `EXPLAIN` in review).
- Use constraints (unique, foreign keys, check) instead of relying on app code only.
- Migrations are small, reversible, and reviewed; no data loss without a documented plan.

## Security

- Validate and bound all input (length, size, enum).
- Authorization checked in services or dependencies, never only in the frontend.
- Never log secrets, tokens or full emails; mask PII.

## Logging

Structured JSON logs with request ID, user ID (if any), route, duration, status. Log at the boundary; do not spam in loops.

## Testing expectations

Unit tests for services and scoring logic, integration tests for each router with a real Postgres, contract tests for provider webhooks using recorded payloads. See [testing.md](testing.md).

## Commit hygiene

Conventional Commits; one logical change per PR; update docs and OpenAPI examples with the change.
