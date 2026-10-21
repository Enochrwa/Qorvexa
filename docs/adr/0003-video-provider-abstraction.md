# ADR-0003: Video provider abstraction

- Status: Proposed (pending customer inputs on content volume, launch target and budget)
- Date: 2026-10-21

## Context

Transcoding, packaging, storage and delivery of video are the main cost and complexity drivers. A $0 budget cannot sustain a real library on any provider. Facts verified 2026-10-21 ([findings](../research/free-tier-findings.md)):

- Mux free plan: 100,000 free delivery minutes per month, unlimited assets, but stored minutes are billed and the player shows a Mux badge.
- Cloudflare R2: 10 GB-month free, free egress; no transcoding.
- Cloudflare Stream: no free tier.
- Cloudflare Pages: 25 MiB per asset; not for video.

## Options considered

1. Mux only: fastest, but vendor lock-in and storage costs.
2. R2 + self-hosted FFmpeg: lowest long-term cost, high engineering and ops load; needs a machine for transcoding.
3. Abstraction with both implementations.

## Decision

Define a `VideoProvider` interface. Implement `LocalProvider` (MinIO + FFmpeg, for dev), `MuxProvider` (pilot) first; add `R2FFmpegProvider` when the customer confirms library size and budget. Frontend only consumes HLS URLs/tokens returned by the API.

## Consequences

- Provider changes do not touch the frontend or catalog.
- Extra code for the abstraction and tests per provider.
- Re-evaluate after the pilot using measured stored and delivered minutes.
