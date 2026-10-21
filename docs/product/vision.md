# Vision and positioning

## Vision

Qorvexa is the place where a viewer opens the site, finds something worth watching in under a minute, watches it without buffering, and always knows what to watch next.

## Problem

Small and mid-size content owners (producers, distributors, regional drama studios) lack an affordable, polished way to host and stream their own catalog. Generic video hosts feel like file lockers, and large streaming platforms are closed to them.

## Target customer

The immediate customer is a content owner who uploads movies and drama series and wants a branded streaming site. The platform should be generic enough to re-brand for other content owners later.

## Value proposition

- For viewers: fast start, adaptive quality, a great player, personalized discovery, resume anywhere.
- For the content owner: a studio to upload, organize, schedule and publish; analytics on what is watched; control over rights and availability.

## Differentiators

1. **Discovery without endless scrolling**: taste onboarding, mood collections, "surprise me", and a short reason for each recommendation.
2. **Drama-aware navigation**: seasons, episodes, recaps, next-unwatched indicator, spoiler-aware descriptions.
3. **Cinematic player**: precise seeking, chapters, subtitle styling, diagnostics, keyboard-first controls.
4. **Admin studio, not an upload form**: resumable uploads, processing states, bulk metadata, scheduling.
5. **Honest, low-cost infrastructure**: provider abstraction so costs can scale with revenue.

## Principles

- Playback reliability beats feature count.
- Never route video bytes through the API server.
- Accessibility and mobile are launch requirements, not extras.
- Collect the minimum personal data needed.
- Optimize for viewers finding content they enjoy, not for trapping them.

## Success metrics

| Area | Metric | Initial target |
|---|---|---|
| Playback | Time to first frame (p75) | under 2.5 s on 4G |
| Playback | Startup failure rate | under 1% |
| Playback | Rebuffer ratio | under 1% of watch time |
| Engagement | Day-7 return rate | track, then set target |
| Engagement | Titles started per active user per week | track, then set target |
| Admin | Upload success rate | over 98% |
| Admin | Upload to Ready time (1 hour episode) | under 15 min |

## Non-goals (initial release)

Native mobile apps, live streaming, DRM, casting, watch parties, payments and subscriptions. See [feature-roadmap.md](feature-roadmap.md) for when these may return.
