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

## Still to verify (Sprint 0)

- Free API host: sleep policy, RAM, bandwidth, terms for video-related traffic.
- Free Postgres: storage cap, connection limits, backup support, retention.
- Free Redis: command/memory limits, or decide to run without it.
- Sentry free quota and sampling needs.
- Domain: price of a `.rw` or `.com` domain if the customer funds one.
