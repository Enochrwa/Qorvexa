# Backend

FastAPI + PostgreSQL service for Qorvexa. Full guide: [docs/backend/README.md](../docs/backend/README.md).

Status: scaffold only; implemented in Sprint 0 and Sprint 1.

```
app/
  core/        config, db, security, errors, logging, rate limiting
  modules/     auth, profiles, catalog, media, playback, engagement, search, admin
  workers/     ARQ settings and jobs
  api/v1/      router aggregation
alembic/       migrations
tests/         unit and integration tests
```
