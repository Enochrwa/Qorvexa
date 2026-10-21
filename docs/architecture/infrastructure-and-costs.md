# Infrastructure and $0 cost model

> Prices and free tiers change. The figures below were checked on 2026-10-21 (see [research/free-tier-findings.md](../research/free-tier-findings.md)). Re-verify against provider pages before presenting numbers to the customer.

## What can be $0

| Item | $0 for | Not $0 when |
|---|---|---|
| Code, repo, CI | Always (GitHub free tier limits apply) | Very heavy CI usage |
| Frontend hosting | Cloudflare Pages free (static app only) | Never put video there; 25 MiB per-asset limit |
| Local dev | Docker Compose (Postgres, Redis, MinIO, Mailpit) | n/a |
| Video pilot | Mux free plan: 100,000 free delivery minutes per month | Storage is billed per stored minute; free plan shows a Mux badge in the player |
| Object storage | Cloudflare R2: 10 GB-month free, zero egress fees | Above 10 GB or above the free operation counts |
| API + database | Free tiers of hosts (cold starts, small storage, limits) | Real traffic, backups, always-on |
| Domain | Free `*.pages.dev` subdomain | Custom domain costs money |

## Reality check on a "$0 streaming platform"

- Storage and delivery always cost something at scale. A $0 setup supports a **small demo/pilot** with a few titles.
- 100 viewers watching 2 hours a day for 30 days is 360,000 delivery minutes, above Mux's 100,000 free minutes.
- On Mux, stored minutes are billed (basic quality listed at $0.003 per minute per month at first-tier rates). Roughly 100 hours of content (6,000 minutes) would be about $18 per month in storage at that rate.
- On R2, 10 GB holds only a handful of full-length movies at multiple renditions.
- Cloudflare Stream has no free tier ($5 per 1,000 minutes stored, $1 per 1,000 minutes delivered).

## Pilot budget plan

| Phase | Content | Delivery | Cost target |
|---|---|---|---|
| Dev (local) | Sample videos on MinIO + FFmpeg | Local | $0 |
| Demo | A few episodes (under ~60 min total) on Mux free or R2 | Under free allowances | $0 |
| Public pilot | Small library, capped renditions | Monitor weekly | Customer-approved, small |
| Launch | Real library | Based on measured minutes | Customer-funded |

## Cost levers

1. Cap max resolution (e.g. 720p) and bitrate ladder.
2. Prefer R2 egress-free storage for self-managed delivery.
3. Use Mux cold storage / delete unused renditions.
4. Disable downloads or limit quality for the pilot.
5. Data-saver default on mobile.
6. Cache catalog and images at the CDN.

## Cost estimator (use with the customer)

Inputs: hours of content, average bitrate, monthly viewer-hours, download share.
- Storage minutes = hours x 60.
- Managed delivery cost = max(viewer-minutes - free minutes, 0) x per-minute rate.
- Self-managed storage GB = hours x 3600 x (sum of ladder bitrates in bits/s) / 8 / 1e9. Example: 1 hour with a 5-rung ladder around 9.4 Mbps total is about 4.2 GB.

Keep a living spreadsheet in `docs/research/` (add when the customer shares real numbers).

## Environments and hosts (candidates, verify limits first)

| Component | Candidate | Notes |
|---|---|---|
| SPA | Cloudflare Pages | Static; global CDN |
| API | A free-tier container/web host | Cold starts; one worker; keep stateless |
| Postgres | A free managed Postgres | Small storage; back up externally |
| Redis | Free-tier managed Redis or run without it initially | Queue and rate limits degrade gracefully |
| Object storage | Cloudflare R2 | S3-compatible |
| Error monitoring | Sentry free tier | Sampling to stay in quota |

See [deployment guide](../devops/deployment-free-tier.md).
