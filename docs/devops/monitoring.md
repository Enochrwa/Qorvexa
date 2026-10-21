# Monitoring and observability

## Signals

| Layer | What | Tool (free-friendly) |
|---|---|---|
| Errors | Backend exceptions, frontend errors, player errors | Sentry free tier (sampled) |
| Logs | Structured JSON with request IDs | Host log viewer; ship to a free log service if needed |
| Metrics | Request rate, latency, error rate, DB pool, job queue depth | Prometheus-style `/metrics` + hosted free dashboard, or host metrics |
| Uptime | `/health` and `/ready` | UptimeRobot-style free monitors |
| Playback QoE | Time to first frame, rebuffer ratio, startup errors, quality distribution | Own `playback_events` + Mux Data (if Mux) |
| Business | Starts, watch time, completion, uploads, searches | Admin analytics from `daily_title_stats` |

## Alerts (initial)

- API error rate above 2% for 5 min.
- p95 latency above 1 s for 10 min.
- Assets stuck in `processing` over 30 min.
- Webhook failures or queue backlog above threshold.
- Startup failure rate above 3% for 15 min.
- Provider usage at 80% of free allowance (check weekly until automated).

## Dashboards

1. Service health. 2. Playback quality. 3. Upload pipeline. 4. Engagement. 5. Cost and usage (delivered minutes, stored minutes/GB).

## Privacy

Telemetry avoids PII; user identifiers are internal IDs; IPs are not stored with events; sampling applied where needed.
