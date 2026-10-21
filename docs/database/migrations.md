# Migrations and data policy

## Alembic workflow

```bash
cd backend
uv run alembic revision --autogenerate -m "add watchlist"
# review the generated file carefully
uv run alembic upgrade head
uv run alembic downgrade -1   # verify reversibility locally
```

## Rules

1. One logical change per migration; descriptive message.
2. Always review autogenerate output (indexes, constraints, enums are often missed).
3. Migrations must be reversible, or explicitly documented as irreversible.
4. Zero-downtime pattern for risky changes: add nullable column -> backfill -> enforce constraint -> drop old.
5. Large index creation on live tables uses `CREATE INDEX CONCURRENTLY` (outside a transaction).
6. CI runs `alembic upgrade head` on a clean database for every PR.
7. Do not edit a migration after it has been merged to `main`; add a new one.

## Seed data

`scripts/seed.py` (Sprint 1) creates: admin user, sample genres, a few titles with placeholder assets for local dev. Never seed demo credentials in production.

## Backups

Free-tier databases may not include reliable backups. Policy: scheduled `pg_dump` to object storage (daily), keep 7 daily + 4 weekly, test a restore monthly. Document the restore runbook in `devops/environments.md` when implemented.

## Privacy

Personal data (email, profile names) is deleted or anonymized on account deletion; analytics tables hold profile IDs only and are purged with the profile.
