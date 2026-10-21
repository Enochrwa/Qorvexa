# System overview

## Context

```
Viewer / Admin browser (React SPA, hosted on a static CDN)
        |                         \
        | JSON over HTTPS          \ HLS segments / MP4 / images (direct, signed)
        v                           v
  FastAPI API  <-------------->  Video provider / object storage + CDN
   |      |  \                      ^
   |      |   \ webhooks / jobs     | direct upload via signed URL
   |      v    v                    |
   |   Redis (cache, queue, rate limits)  Admin uploads (resumable)
   v
 PostgreSQL (source of truth)
```

Rules:

1. **Video bytes never pass through the API.** Uploads go directly to storage/provider with a signed URL; playback is served by the provider/CDN.
2. **The API owns metadata, auth, authorization and playback access decisions.**
3. **Providers are replaceable** behind a `VideoProvider` interface ([ADR-0003](../adr/0003-video-provider-abstraction.md)).
4. **Modular monolith first**: one FastAPI app with clear modules; extract services only with evidence.

## Backend modules

| Module | Responsibility |
|---|---|
| `auth` | Registration, login, refresh, password reset, email verification, roles |
| `profiles` | Profiles, preferences, maturity limits |
| `catalog` | Titles, seasons, episodes, genres, people, collections |
| `media` | Assets, upload sessions, provider webhooks, subtitles, playback authorization |
| `playback` | Watch progress, history, playback events (QoE) |
| `engagement` | Watchlist, ratings, notifications, recommendations |
| `search` | Postgres full-text and trigram search |
| `admin` | Studio endpoints, analytics, moderation |
| `core` | Config, db session, security, logging, errors, rate limiting |

## Frontend areas

Public browse, title detail, player, account/profile, watchlist/history, admin studio. See [frontend/README.md](../frontend/README.md).

## Key flows

### Upload and publish
1. Admin creates a title/episode (draft).
2. Frontend requests an upload session: `POST /admin/media/uploads`.
3. API creates a `media_assets` row (`uploading`), asks the provider for a signed/direct upload URL, returns it.
4. Browser uploads directly (chunked/resumable) and reports progress.
5. Provider webhook (or worker polling) moves the asset to `processing` then `ready`, storing playback ID, duration, renditions.
6. Admin previews, then publishes or schedules; scheduler flips status at the publish time.

### Playback
1. `GET /titles/{id}` returns metadata and the next episode to play.
2. `POST /playback/sessions` authorizes (maturity limit, availability, publish state) and returns a playback URL/token.
3. Player streams HLS from the provider/CDN; reports progress every 10 s and on pause/close.
4. `playback_events` feed QoE and engagement analytics.

## Recommendations

Rule-based score per candidate title per profile:

`score = w_g*genre + w_l*language + w_t*theme_cast + w_p*popularity + w_r*freshness`

Initial weights (3, 2, 2, 1, 1) are placeholders and are tuned from pilot data. A diversity pass limits repeated genres per row. Candidates exclude finished titles and respect maturity limits. Precompute per profile into a cache table on a schedule; fall back to popular-by-genre for new profiles.

## Search

PostgreSQL `tsvector` plus `pg_trgm` for typo tolerance, indexed on title, original title, cast and tags. Move to a dedicated search engine only if measurements demand it.

## Caching

- CDN caching for static assets and images.
- API: short-lived cache (Redis) for public catalog rows, invalidated on publish/unpublish.
- ETags and `Cache-Control` for public GETs.

## Failure behavior

- API down: SPA shows cached catalog shell and clear retry messages; already-playing streams continue.
- Provider webhook missed: reconciliation job polls assets stuck in `processing`.
- Redis down: rate limiting fails open for reads, closed for auth endpoints; queue paused with alert.
