# Product backlog

Ordered roughly by priority within each group. IDs map to [requirements](../product/requirements.md). Move items into a sprint during planning.

## Launch candidates (not yet scheduled in detail)

- Account deletion and data export (FR-A4)
- Notification preferences scaffolding (FR-E3 groundwork)
- Admin user management (roles, suspend)
- Content reporting (FR-S8 groundwork)
- Open Graph preview pages for shared title links (see ideas)

## Next

| Item | Req | Size |
|---|---|---|
| Multiple audio tracks | FR-P7 | L |
| Chapters and seek thumbnails | FR-P8 | L |
| Playback diagnostics overlay | FR-P9 | M |
| Bulk metadata import (CSV) | FR-S6 | L |
| Admin analytics dashboard | FR-S7 | XL |
| Moderation queue | FR-S8 | M |
| New-episode notifications (email + in-app) | FR-E3 | L |
| Episode release calendar | FR-E4 | M |
| Social share with timestamp | FR-E5 | S |
| Download quality selection | FR-D2 | M |
| Ratings and reviews polish and moderation | FR-C6 | M |
| Scheduling polish (time zones, bulk schedule) | FR-S4 | M |

## Later

Browser offline library (FR-D3), casting (FR-P10), DRM, watch parties, semantic search (FR-C9), AI summaries/chapters, social login (FR-A5), payments and subscriptions, native apps, multi-tenant white-label.

## Technical debt and chores

- Storybook for design system
- Load-test baselines in CI (nightly)
- Typed event schema for `playback_events`
- Replace polling reconciliation with provider event streaming where possible
