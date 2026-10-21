# Requirements

IDs are stable; reference them in issues, PRs and tests. Priority: **M** (must, launch), **S** (should, next), **C** (could, later).

## Functional requirements

### Accounts and profiles
| ID | Requirement | P |
|---|---|---|
| FR-A1 | Register, verify email, log in, log out, reset password | M |
| FR-A2 | Multiple profiles per account (name, avatar, language, maturity limit) | M |
| FR-A3 | Roles: viewer, editor, admin | M |
| FR-A4 | Account deletion and data export | S |
| FR-A5 | Social login (Google) | C |

### Catalog and discovery
| ID | Requirement | P |
|---|---|---|
| FR-C1 | Movies, series, seasons, episodes with rich metadata | M |
| FR-C2 | Home page with curated and personalized rows | M |
| FR-C3 | Search by title, cast, genre, language, year with typo tolerance | M |
| FR-C4 | Filter, sort and paginate browse pages | M |
| FR-C5 | Watchlist and favorites | M |
| FR-C6 | Ratings and reviews | S |
| FR-C7 | Mood collections and "surprise me" | S |
| FR-C8 | Related titles | S |
| FR-C9 | Semantic search | C |

### Playback
| ID | Requirement | P |
|---|---|---|
| FR-P1 | Adaptive HLS playback with automatic quality | M |
| FR-P2 | Manual quality, speed 0.5x to 2x, volume, seek, fullscreen | M |
| FR-P3 | Captions and subtitle styling | M |
| FR-P4 | Resume position across devices | M |
| FR-P5 | Next episode and skip intro/recap (marker-based) | M |
| FR-P6 | Picture-in-picture, keyboard shortcuts, touch gestures | M |
| FR-P7 | Multiple audio tracks | S |
| FR-P8 | Chapters and thumbnail previews on the seek bar | S |
| FR-P9 | Playback diagnostics overlay | S |
| FR-P10 | Casting | C |

### Downloads
| ID | Requirement | P |
|---|---|---|
| FR-D1 | Authorized MP4 download with range/resume support, per-title permission | M |
| FR-D2 | Download quality selection | S |
| FR-D3 | Browser offline library (supported browsers) | C |

### Admin studio
| ID | Requirement | P |
|---|---|---|
| FR-S1 | Resumable, direct-to-storage uploads with progress and retry | M |
| FR-S2 | Processing states: Uploading, Processing, Ready, Published, Failed | M |
| FR-S3 | Metadata, poster, backdrop and subtitle editor | M |
| FR-S4 | Draft, schedule and publish; unpublish | M |
| FR-S5 | Series, season and episode management with reorder | M |
| FR-S6 | Bulk import and edit metadata | S |
| FR-S7 | Analytics: starts, watch time, completion, failures, searches | S |
| FR-S8 | Moderation queue and content reports | S |

### Engagement
| ID | Requirement | P |
|---|---|---|
| FR-E1 | Continue watching row | M |
| FR-E2 | Personalized recommendations (rule-based scoring) | M |
| FR-E3 | New-episode and release notifications (opt-in) | S |
| FR-E4 | Episode release calendar | S |
| FR-E5 | Social sharing with timestamp links | S |

## Non-functional requirements

| ID | Area | Requirement |
|---|---|---|
| NFR-1 | Performance | Catalog API p95 under 300 ms; home page LCP under 2.5 s on mid-range mobile over 4G |
| NFR-2 | Playback | Time to first frame p75 under 2.5 s; rebuffer ratio under 1% |
| NFR-3 | Upload | Resume after interruption; no video bytes through the API |
| NFR-4 | Availability | Target 99.5% during pilot; graceful degradation if the API is down (cached catalog) |
| NFR-5 | Security | OWASP ASVS L1 baseline; see [security](../security/security.md) |
| NFR-6 | Accessibility | WCAG 2.2 AA for core flows; keyboard-operable player; captions |
| NFR-7 | Browser support | Last 2 versions of Chrome, Edge, Firefox, Safari; iOS Safari and Android Chrome |
| NFR-8 | Responsiveness | Mobile-first, 360 px up to 4K TV |
| NFR-9 | Privacy | Minimum data; consent for notifications; deletion on request |
| NFR-10 | Observability | Errors, request metrics and playback QoE metrics collected |
| NFR-11 | Portability | Video provider replaceable behind an interface |
| NFR-12 | Cost | Prototype runs on free tiers; cost per delivered hour is tracked |
