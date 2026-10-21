# ADR-0011: Cloudinary for pilot video, posters and thumbnails

- Status: Accepted by the owner on 2026-10-21, with a documented capacity risk
- Date: 2026-10-21
- Deciders: Enochrwa
- Amends: [ADR-0003](0003-video-provider-abstraction.md) (Cloudinary replaces Mux as the pilot provider)

## Context

The owner chose Cloudinary on the Free plan to store and deliver movies, posters and thumbnails, monitoring usage and getting customer approval before any spend.

Verified 2026-10-21 against Cloudinary's documentation ([billing and plans](https://cloudinary.com/documentation/billing_and_plans), [credits FAQ](https://cloudinary.com/documentation/developer_onboarding_faq_credits)):

- Free plan: **25 credits per month**, shared across storage, bandwidth and transformations.
- 1 credit = 1 GB managed storage, or 1 GB delivered bandwidth, or 1,000 transformations. Video transformations are counted per second processed, by resolution.
- For video, 1 GB of delivery is roughly 500 seconds of SD or 250 seconds of HD (Cloudinary's figure).
- Storage includes cached derived assets, not only the originals. Free-plan video bandwidth is counted at 1 GB per credit; limits are described as soft.
- Not verified: maximum upload file size on Free, and whether Cloudinary's terms allow running a full streaming service on the Free plan. Check both before the first upload.

## Capacity math (what the Free plan really allows)

If 5 credits go to storage and 20 to video delivery: about 20 GB, roughly 10,000 seconds of SD (about 2.8 hours) or 5,000 seconds of HD (about 1.4 hours) of **total viewing per month across all viewers**. A pilot of tens of viewers watching one film each will likely exceed this. By comparison, Mux's free plan gives 100,000 delivery minutes per month but bills storage.

## Decision

- Add a `CloudinaryProvider` behind the existing `VideoProvider` interface (ADR-0003). Frontend still consumes only HLS URLs returned by the API.
- Posters, backdrops and thumbnails also go to Cloudinary; always request resized derived images (width, format `auto`) to limit transformations.
- Start on the Free plan. **No paid plan, overage or add-on without owner and customer approval.**
- Add a usage guard in Sprint 2: read usage from the Cloudinary Admin API, show it in the admin studio, warn at 70% and block new uploads at 90% of the monthly credits.
- Use low-ladder, low-bitrate encodes (mobile-first) to stretch delivery.
- Keep `LocalProvider` for development and tests; keep Mux and R2+FFmpeg as documented alternatives.

## Consequences

- The free allowance supports a technical demo and a very small private pilot, not a public pilot of tens to hundreds of viewers. The pilot size must be capped (invite-only, short library) or the plan funded. Decision needed before public launch (see STATUS.md).
- Credentials (`CLOUDINARY_URL` or cloud name, API key, API secret) live only in environment variables; never committed.
- Signed upload parameters are generated server-side; video bytes never pass through the FastAPI API.
- Re-verify limits at the start of every sprint.

## Update 2026-10-21: scope and usage guard

- Cloudinary is for development and a tiny, invite-only pilot only. Do not assume the Free plan can serve tens or hundreds of viewers.
- Before public launch, verify: upload-size limits, streaming-service terms, storage allowance and delivery cost. If the Free allowance is insufficient, present the customer with a cost estimate and get approval before upgrading.
- The `VideoProvider` abstraction stays, so the provider can be switched without rewriting the application.
- Usage guard (Sprint 2), built only if usage can be measured reliably from the Cloudinary Admin API:
  - `CLOUDINARY_WARN_PERCENT` (default 70) shows a warning in the admin studio.
  - `CLOUDINARY_BLOCK_PERCENT` (default 90) blocks new uploads.
  - **Fail safe:** if usage data is unavailable or stale, new uploads are blocked and the admin sees why; playback is not affected.
  - **These safeguards do not guarantee Cloudinary will never charge.** They only watch usage Cloudinary reports, which can lag; delivery by viewers is not something we can block per request. Paid overage or an upgrade still requires explicit owner and customer approval.
- Credentials only in environment variables or the platform's secret manager; never in chat, commits, logs or docs.
