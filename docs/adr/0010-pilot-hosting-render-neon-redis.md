# ADR-0010: Pilot hosting on Render, Neon and owner-managed Redis

- Status: Accepted (owner approved 2026-10-21)
- Date: 2026-10-21
- Deciders: Enochrwa

## Context

Budget is $0 ([findings](../research/free-tier-findings.md), verified 2026-10-21). The pilot is small (tens to low hundreds of viewers).

## Decision

- API: Render free web service. Frontend: Cloudflare Pages (SPA only, never video).
- Postgres: Neon Free (0.5 GB, 100 CU-hours per month, scale to zero).
- Redis: the owner provisions and manages a real Redis instance and supplies `REDIS_URL`. ARQ stays as the job system (ADR-0006). No Redis provider is chosen or paid for by this project.

## Cost

$0 for the project. Redis cost, if any, is carried by the owner outside this repository.

## Consequences

- Cold starts (about a minute) after 15 idle minutes on Render; show a waking-up state in the UI. No keep-alive pings.
- Render has no free background worker: until one is funded, run ARQ where the owner's Redis and a worker process are available, or run the worker locally for the pilot.
- Neon 0.5 GB cap: set retention for events and watch progress; keep external backups (R3).
- Re-verify limits each sprint start.
