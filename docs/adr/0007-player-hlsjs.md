# ADR-0007: Player built on hls.js with custom React controls

- Status: Accepted
- Date: 2026-10-21

## Context

We need adaptive HLS playback, full control of UI, and a path to captions, multiple audio tracks and diagnostics. Mux Player is convenient but ties UI to a provider (and shows a badge on the free plan).

## Decision

Use hls.js (native HLS on Safari/iOS) behind a `<QorvexaPlayer />` component with our own controls. Evaluate Shaka Player later if browser offline storage or DASH becomes a requirement.

## Consequences

More UI work, but consistent UX across providers and full feature control. See [player-spec.md](../frontend/player-spec.md).
