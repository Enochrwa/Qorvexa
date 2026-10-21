# Performance and scalability

## Budgets

| Area | Budget |
|---|---|
| Home page LCP (mid-range mobile, 4G) | under 2.5 s |
| Initial JS (route-level) | under 200 KB gzip for browse routes; player code lazy-loaded |
| Catalog API p95 | under 300 ms |
| Time to first frame p75 | under 2.5 s |
| Rebuffer ratio | under 1% |
| Search response p95 | under 200 ms |

## Frontend

- Route-based code splitting; lazy-load player, admin studio and chart libraries.
- Responsive images (`srcset`), modern formats (AVIF/WebP), blur-up placeholders, `loading="lazy"`.
- Prefetch title data on hover/focus; prefetch player chunk on title page.
- TanStack Query caching with stale-while-revalidate; virtualized long lists.
- PWA: cache app shell and catalog images; offline-friendly error pages.

## Backend

- Async FastAPI with asyncpg; connection pooling sized to host limits.
- Indexes for: title slug, genre joins, `published_at`, watch progress `(profile_id, updated_at)`, search vectors, trigram indexes.
- Keyset (cursor) pagination for large lists; avoid `OFFSET` on big tables.
- Cache public rows in Redis (30-120 s TTL); invalidate on publish.
- Batch progress writes: coalesce updates; one upsert per profile/asset per interval.
- Rate limit by IP and account; stricter on auth.

## Video delivery

- Adaptive ladder with a low starting rendition for fast start; player `startLevel` heuristic.
- 4-6 s segments; preload next segments within buffer targets; avoid over-buffering to limit wasted delivery minutes.
- CDN with range request support for downloads.

## Scalability path

1. Single API instance + Postgres + managed video (pilot).
2. Scale API horizontally (stateless), add read replica or caching.
3. Move recommendations and analytics to scheduled jobs and materialized views.
4. Extract workers and analytics into separate services only when measured necessary.

## Load testing

Use k6 against catalog, search and playback-session endpoints. Targets and scripts live in `scripts/loadtest/` (to be added in Sprint 5).
