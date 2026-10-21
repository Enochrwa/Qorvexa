# Database schema (PostgreSQL)

All tables: `id uuid pk`, `created_at timestamptz default now()`, `updated_at timestamptz` unless noted. Extensions: `pgcrypto` or UUID generation, `pg_trgm`, `citext`.

## Entity relationship (summary)

```
users 1─* profiles 1─* watch_progress *─1 media_assets *─1 episodes *─1 seasons *─1 titles
profiles 1─* watchlist *─1 titles       titles *─* genres (title_genres)
profiles 1─* ratings   *─1 titles       titles *─* people (title_people)
titles 1─* collections_items *─1 collections
media_assets 1─* subtitle_tracks        media_assets 1─* upload_sessions
```

## Tables

### Identity
| Table | Key columns |
|---|---|
| `users` | email (citext, unique), password_hash, role (`viewer|editor|admin`), status (`active|suspended|deleted`), email_verified_at |
| `refresh_tokens` | user_id, family_id, token_hash (unique), expires_at, revoked_at, replaced_by |
| `profiles` | user_id, name (unique per user, case-insensitive), avatar (preset key `avatar-1..12`), language, maturity_limit (`all|7+|13+|16+|18+`), autoplay_next bool, data_saver bool, subtitle_prefs jsonb (`enabled`, `language`, `size`) |
| `one_time_tokens` | user_id, purpose, token_hash, expires_at, used_at |

### Catalog
| Table | Key columns |
|---|---|
| `titles` | slug (unique), type (`movie|series`), name, original_name, synopsis, release_year, maturity_rating, language, country, poster_url, backdrop_url, trailer_asset_id, status (`draft|scheduled|published|archived`), publish_at, available_until, downloads_enabled, search_document tsvector |
| `seasons` | title_id, number, name, synopsis; unique (title_id, number) |
| `episodes` | season_id, number, name, synopsis, runtime_seconds, air_date, intro_start/intro_end/recap_end (seconds, nullable), status; unique (season_id, number) |
| `genres` | name, slug (unique) |
| `title_genres` | title_id, genre_id (pk composite) |
| `people` | name, slug |
| `title_people` | title_id, person_id, role (`actor|director|writer`), billing_order |
| `collections` | name, slug, description, kind (`editorial|mood`), sort_order, is_active |
| `collection_items` | collection_id, title_id, position |

### Media
| Table | Key columns |
|---|---|
| `media_assets` | owner_type (`movie|episode|trailer`), owner_id, provider, provider_asset_id, playback_id, status (`created|uploading|uploaded|processing|ready|failed|deleted`), failure_reason, duration_seconds, source_size_bytes, checksum, renditions jsonb, thumbnails jsonb |
| `upload_sessions` | asset_id, uploader_id, provider_upload_id, expires_at, bytes_received, state |
| `subtitle_tracks` | asset_id, language, label, format (`vtt`), url, is_default |
| `audio_tracks` | asset_id, language, label, is_default |
| `provider_events` | provider, event_id (unique per provider), type, payload jsonb, processed_at |

### Viewing and engagement
| Table | Key columns |
|---|---|
| `watch_progress` | profile_id, asset_id, position_seconds, duration_seconds, completed bool, updated_at; unique (profile_id, asset_id) |
| `watch_history` | profile_id, title_id, episode_id, started_at, last_watched_at, completed_at |
| `watchlist` | profile_id, title_id; unique (profile_id, title_id) |
| `ratings` | profile_id, title_id, score smallint check 1..5, review text; unique (profile_id, title_id) |
| `notifications` | profile_id, type, payload jsonb, channel, status, read_at, sent_at |
| `notification_prefs` | profile_id, type, enabled, quiet_hours jsonb |
| `recommendation_cache` | profile_id, row_key, title_ids uuid[], reason jsonb, generated_at |
| `reports` | reporter_profile_id, title_id, reason, details, status |

### Analytics
| Table | Key columns |
|---|---|
| `playback_events` | session_id, profile_id, asset_id, event (`start|first_frame|rebuffer|quality_change|error|end`), value numeric, ts. Partition by month; prune after 30-90 days |
| `daily_title_stats` | date, title_id, starts, watch_seconds, completions, unique_viewers |
| `search_queries` | normalized_query, results_count, ts (aggregated daily; avoid raw PII) |

## Indexes (initial)

- `titles(slug)`, `titles(status, publish_at)`, GIN on `titles.search_document`, GIN trigram on `titles.name`.
- `title_genres(genre_id, title_id)`, `episodes(season_id, number)`.
- `watch_progress(profile_id, updated_at desc)`.
- `watchlist(profile_id, created_at desc)`.
- `media_assets(status, updated_at)` for reconciliation.
- `playback_events(asset_id, ts)` per partition.

## Constraints and integrity

- Foreign keys with `ON DELETE CASCADE` only for owned children (profiles -> progress).
- Check constraints on enums (or Postgres enum types), rating range, non-negative positions.
- Soft delete for users (`status = deleted`) with scheduled hard-delete job for privacy.

## Retention

| Data | Retention |
|---|---|
| `playback_events` raw | 30-90 days, then aggregated |
| `provider_events` | 90 days |
| Expired tokens | purge daily |
| Deleted accounts | purge personal data within 30 days |
