# ADR-0006: Background jobs with ARQ

- Status: Accepted
- Date: 2026-10-21

## Context

Webhook processing, reconciliation, scheduled publishing, recommendation precompute, notifications and (self-managed) transcoding must run outside request handlers.

## Decision

Use ARQ (asyncio, Redis-backed) with cron jobs. Jobs are idempotent and carry explicit retry policy.

## Alternatives

Celery (heavier), RQ (sync), Postgres-backed queues (no Redis dependency). If free-tier Redis proves unreliable, switch to a Postgres-backed queue; job code stays the same because handlers are plain async functions.

## Consequences

Redis becomes a dependency. A free-tier fallback: run in-process scheduler for the demo only.
