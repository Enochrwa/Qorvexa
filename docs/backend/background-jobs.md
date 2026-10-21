# Background jobs

Decision: [ADR-0006](../adr/0006-background-jobs-arq.md). Worker entrypoint: `app.workers.settings.WorkerSettings`.

## Jobs

| Job | Trigger | Purpose | Idempotency key |
|---|---|---|---|
| `process_provider_event` | Webhook | Update asset state, store duration/renditions | Provider event ID |
| `reconcile_assets` | Cron (5 min) | Re-check assets stuck in uploading/processing | Asset ID + state |
| `publish_scheduled` | Cron (1 min) | Publish titles/episodes whose `publish_at` passed | Title ID + publish_at |
| `transcode_asset` | After upload (self-managed only) | FFmpeg ladder, HLS packaging, thumbnails | Asset ID |
| `generate_recommendations` | Cron (hourly) / on demand | Precompute per-profile rows | Profile ID + run ID |
| `send_notifications` | Cron / event | New-episode emails and in-app notifications, honoring opt-in and quiet hours | Notification ID |
| `prune_events` | Cron (daily) | Aggregate and delete old `playback_events` | Date |
| `cleanup_uploads` | Cron (daily) | Remove abandoned upload sessions and orphan files | Session ID |

## Rules

- Handlers are plain async functions; no HTTP types.
- At-least-once delivery: every job must be safe to run twice.
- Explicit retries with exponential backoff; dead jobs are logged and alerted.
- Long jobs report progress to the asset row for the admin UI.
- Enqueue after the DB transaction commits (outbox pattern if needed).
- Local fallback: if Redis is unavailable in demo, run a minimal in-process scheduler for cron jobs only.
