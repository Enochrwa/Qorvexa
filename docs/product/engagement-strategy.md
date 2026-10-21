# Engagement and retention strategy

Goal: help viewers find and finish content they enjoy, and give them honest reasons to return. No dark patterns.

## Loops

| Loop | Mechanism | Metric |
|---|---|---|
| Resume | Continue watching row, resume across devices | Resume starts per active user |
| Binge | Next-episode countdown, "next unwatched" button | Episodes per session |
| Discover | Taste onboarding, personalized rows, mood collections, surprise me | Starts from home rows |
| Return | Opt-in new-episode notifications, release calendar | D7 return, notification opt-in rate |
| Share | Timestamp links, share cards | Visits from shared links |
| Curate | Owner-made collections and editorial playlists | Collection starts |

## Recommendation approach (v1)

Rule-based SQL scoring (genre, language, cast/theme, popularity, freshness) with a diversity rule so no row is dominated by one genre. See [architecture/overview.md](../architecture/overview.md#recommendations). Weights are tunable configuration, validated against pilot data.

## Guardrails

- Notifications are opt-in with per-type controls and quiet hours.
- Autoplay and autoplay-next are user-controllable.
- Data collected: watch events needed for progress, recommendations and QoE. No third-party ad trackers.
- Recommendations can be reset by the viewer.

## Experiments (after pilot)

Row order, autoplay countdown length, taste picker length, thumbnail style. Use feature flags and measure start rate and completion rate.
