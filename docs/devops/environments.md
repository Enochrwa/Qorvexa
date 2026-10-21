# Environments

| Env | Purpose | Data | Deploy |
|---|---|---|---|
| local | Development | Seed/sample, MinIO storage | `docker compose up` + dev servers |
| ci | Automated checks | Ephemeral Postgres/Redis | GitHub Actions |
| preview | Per-PR frontend previews (Cloudflare Pages) | Points at staging API | Automatic |
| staging | Demo and pilot rehearsal | Non-sensitive test data | Auto-deploy from `main` |
| production | Real users | Real data | Manual approval (tag) |

## Configuration

All configuration via environment variables ([.env.example](../../.env.example)). Secrets live in the host's secret manager and GitHub Actions secrets, never in the repo. Separate credentials per environment.

## Secrets management

- Rotate JWT secret and provider keys at least yearly and on suspected exposure.
- Principle of least privilege for storage keys (bucket-scoped).
- If a secret is pasted into chat, issue tracker or a commit, treat it as leaked: revoke it immediately.

## Backups and restore (runbook placeholder)

1. Daily `pg_dump` uploaded to object storage (encrypted).
2. Monthly restore drill into a scratch database.
3. Document restore time and steps here after the first drill.

## Domains

Pilot: free `*.pages.dev` for the SPA and the API host's default domain. Production: custom domain with the SPA and API on sibling subdomains (e.g. `app.` and `api.`) so cookies work with `SameSite`.
