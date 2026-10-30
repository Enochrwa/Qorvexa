# Free-tier deployment guide

> Free tiers change. Before choosing a host, check its current limits (sleep behavior, RAM, storage, bandwidth, terms about video and commercial use). Record what you verified in [research/free-tier-findings.md](../research/free-tier-findings.md).

## Target topology (pilot)

```
Browser  ->  One Render web service (Docker image: FastAPI + the built web app)  ->  Neon Postgres (free)
                       |                                                              Redis (owner-managed)
                       +-> Video provider (Cloudinary on the free plan for development and a tiny pilot)
```

The web app and the API share one origin on purpose: the session cookie is not stored by browsers when they are on different sites ([ADR-0015](../adr/0015-serve-frontend-from-api.md), evidence in [browser-measurements](../research/browser-measurements.md)).

## The service (web app + API)

- Image: `infra/docker/backend.Dockerfile` (builds the frontend, then the API; non-root; health check on `/health`). Or build natively: `cd frontend && VITE_API_URL= npm run build`, then start `uvicorn app.main:app` with `FRONTEND_DIST_DIR` pointing at `frontend/dist`.
- Required environment (secrets in the host's secret manager, never in the repo):
  `APP_ENV=production`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET` (random, 32+ characters), `COOKIE_SECURE=true`, `FRONTEND_URL` (the public https address, used in emails), `FRONTEND_DIST_DIR` (already set in the image), `TRUSTED_PROXY_COUNT` (see below), SMTP settings for a real mail provider.
- `CORS_ORIGINS` is not needed (same origin). Leave it unset.
- `TRUSTED_PROXY_COUNT`: set it to the number of proxies in front of the app (Render: probably 1) only after checking how the host appends `X-Forwarded-For`. Too low and everyone shares one rate-limit bucket; too high and clients can spoof their address.
- Health check path `/health`; readiness `/ready` (database and Redis).
- Free tiers sleep when idle. The first request after a pause waits for a cold start (reported at about a minute; not measured by us). Mitigations: a "waking up" state in the UI, and a keep-alive pinger only if the host's terms allow it.
- One instance: `uvicorn --workers 1` (the in-process rate-limit fallback is per process).

## Alternative: app on a CDN, API elsewhere

Only works if both are on the **same site** (for example `app.example.com` and `api.example.com`), which needs a domain. Leave `FRONTEND_DIST_DIR` unset, set `CORS_ORIGINS` to the app's origin, build the app with `VITE_API_URL` set to the API's address. Cloudflare Pages notes: build command `npm run build`, output `dist`, root `frontend`, SPA fallback `/* /index.html 200`; 500 builds per month and 20,000 files on the free plan; never host video there.

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
