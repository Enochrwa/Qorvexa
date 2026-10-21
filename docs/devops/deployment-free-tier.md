# Free-tier deployment guide

> Free tiers change. Before choosing a host, check its current limits (sleep behavior, RAM, storage, bandwidth, terms about video and commercial use). Record what you verified in [research/free-tier-findings.md](../research/free-tier-findings.md).

## Target topology (pilot)

```
Cloudflare Pages (SPA)  ->  API host (FastAPI container, 1 instance)  ->  Managed Postgres (free tier)
                                  |                                      Redis (free tier or optional)
                                  +-> Video provider (Mux free plan or R2 + worker)
```

## Frontend: Cloudflare Pages

- Connect the repo, build command `npm run build`, output `dist`, root `frontend`.
- Set `VITE_API_URL`. Add SPA fallback via `_redirects` (`/* /index.html 200`).
- Limits to remember: 500 builds per month on the free plan, 20,000 files and 25 MiB per asset per site. Do not host video here.

## API host

Requirements: container or Python runtime, env vars, HTTPS, health check. Expect cold starts on free tiers; mitigations: lightweight startup, keep-alive pinger only if the host's terms allow it, and a "waking up" UI state.

Dockerfile (to be added in Sprint 0): multi-stage, non-root user, `uvicorn --workers 1` (increase with plan), healthcheck on `/health`.

## Database

Free managed Postgres has small storage and may lack backups: keep `playback_events` pruned, use the external `pg_dump` backup routine ([environments.md](environments.md)).

## Redis

If no free Redis is acceptable, run the pilot with in-process rate limiting and Postgres-backed jobs (see [ADR-0006](../adr/0006-background-jobs-arq.md)).

## Video

- Mux: create an access token, configure the webhook to `/api/v1/webhooks/mux`, enable signed playback if used.
- R2: create a bucket, an API token scoped to it, CORS for the SPA origin, public access via a custom domain or signed URLs.

## Go-live checklist

- [ ] Env vars set per environment, secrets not in repo
- [ ] Migrations applied; admin user created via script
- [ ] CORS and cookie settings verified across the SPA and API domains
- [ ] HTTPS everywhere; HSTS enabled
- [ ] Rate limits on; Sentry DSN set
- [ ] Backups running and a restore tested
- [ ] Privacy policy, terms, takedown contact published
- [ ] Load and playback smoke tests passed on real devices
- [ ] Budget alert/usage check on provider dashboards
