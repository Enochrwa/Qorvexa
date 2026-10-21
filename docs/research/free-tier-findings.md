# Free-tier findings (verified 2026-10-21)

Sources are official docs or provider announcements where possible. Re-verify before relying on any number; provider terms change.

## Mux Video

- Free plan: 100,000 free delivery minutes per month; the free minutes apply across all resolutions (announcement, 2025).
- Free plan has unlimited assets (an earlier draft plan in our notes claimed "10 assets"; that is **outdated** and was corrected).
- Free-plan videos display a small Mux badge in Mux Player.
- Storage is billed per stored minute (basic tier first-tier rate listed at $0.003 per minute per month). Input/encoding for basic assets is free. Delivery beyond the free minutes is listed starting at $0.001 per minute at first-tier rates.
- Practical implication: delivery is free up to a point, but storage of a large library is not free.
- Sources: https://www.mux.com/blog/free-plan, https://www.mux.com/blog/price-drop, https://www.mux.com/pricing.md

## Cloudflare R2

- Free tier: 10 GB-month standard storage, 1 million Class A operations, 10 million Class B operations per month; egress is free. Usage above is billed.
- R2 is object storage only: no transcoding or HLS packaging.
- Source: https://www.cloudflare.com/plans.md and R2 pricing docs.

## Cloudflare Stream

- No free tier: $5 per 1,000 minutes stored (prepaid), $1 per 1,000 minutes delivered; encoding and ingress included. Preloading and buffering count as delivery.
- Source: https://developers.cloudflare.com/stream/pricing

## Cloudflare Pages

- Free plan: 500 builds per month, 20,000 files per site, 25 MiB maximum per asset.
- Do not host video on Pages; use object storage or a video service. Cloudflare's terms restrict using the CDN/Pages for non-HTML large-file/video distribution on standard plans (third-party summaries; read the current ToS before relying on this).
- Source: https://developers.cloudflare.com/pages/platform/limits

## Corrections to the earlier external plan

| Earlier claim | Status |
|---|---|
| Mux free plan includes up to 10 assets | Outdated; unlimited assets, but storage is billed |
| Mux gives a complete $0 solution for a library | Not true; storage and over-100k delivery cost money |
| Cloudflare Pages is fine for the React app | True for the SPA only |
| R2 is a complete streaming solution | Not true; you must build transcoding and packaging |
| "$0 domain" is possible | Only with free subdomains (e.g. `*.pages.dev`) |
| Free backend/DB hosting | Not covered by the plan; candidates must be verified (cold starts, storage, backups) |

## API host candidates (verified 2026-10-21)

### Render (free web service, free Key Value)
- 750 free instance hours per workspace per month; a free web service spins down after 15 minutes without inbound traffic, and resumes on the next request (about 1 minute for a cold start per third-party reports; Render's own community staff say it depends on the app).
- Ephemeral filesystem; may be restarted at any time; free services cannot attach disks; Hobby workspace includes 5 GB outbound bandwidth then $0.15 per GB, 500 pipeline minutes.
- Render says artificially keeping a free service awake goes against the spirit of the free tier. Do not use keep-alive pings.
- Background workers and private services have **no free tier** (from $5 per month), so an always-on ARQ worker is not free here. Run jobs in-process or on a schedule for the pilot, or accept a paid worker.
- Free Postgres on Render is a 1 GB database that **expires after 30 days** (per a September 2026 third-party summary). Not suitable as the primary store.
- Sources: https://render.com/docs/free, https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses, https://flaviocopes.com/hosting-free-tiers/ (third party)

### Fly.io
- No free allowance: a 7-day trial with 2 hours of machine runtime, then a card is required (third-party summary, September 2026). Excluded under the $0 rule.

## Postgres candidate: Neon Free
- Permanent free plan, no card. Per project: 0.5 GB storage, 100 CU-hours per month, autoscaling up to 2 CU, compute suspends after 5 minutes idle. Hitting a monthly limit suspends compute until the next month.
- Restore window 6 hours on Free. PgBouncer connection pooling is included.
- Fit: fine for Sprints 0 to 3 and a small catalog. 0.5 GB is tight once watch progress and events grow; plan retention and external backups (R3).
- Source: https://neon.com/pricing
- Alternative: Supabase Free (2 projects, 500 MB each, pauses after a week idle) per Neon's comparison page; not verified on Supabase's own site.

## Redis candidate: Upstash Free
- 256 MB data, **500K commands per month**, 10,000 commands per second, one free database per account.
- **Risk:** ARQ polls Redis continuously. At its default polling interval an idle worker alone can exceed 500K commands per month. Either raise `poll_delay`, run the queue on Postgres for the pilot, or drop Redis from the pilot. Needs a decision (see STATUS.md, question Q3).
- Source: https://upstash.com/pricing/redis
- Render Key Value free instances exist; their limits were not verified on an official page this run.

## Sentry
- Developer plan: free, 1 user, 5,000 errors per month, 5M spans, 50 replays (third-party summaries; not checked on sentry.io directly). Enough for a solo pilot with sampling.

## Domain
- Not verified. Pilot uses free subdomains (`*.pages.dev`, the host's default). Ask the customer before budgeting a `.rw` or `.com`.

## Verdict for Sprint 0
$0 hosting of the **API + Postgres + Redis + worker** is possible only with compromises: cold starts (Render), 0.5 GB database (Neon), a command-capped Redis (Upstash) and no free background worker. No paid service has been added. Recorded in STATUS.md as decisions to approve.
