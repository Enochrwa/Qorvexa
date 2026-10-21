# Player specification

Decision: [ADR-0007](../adr/0007-player-hlsjs.md). Component: `<QorvexaPlayer />` in `src/features/player/`.

## Architecture

```
QorvexaPlayer
├── usePlayerEngine()    wraps hls.js / native HLS, exposes state + commands
├── usePlayerState()     reducer: playing, buffering, time, buffered, level, rate, volume, tracks, error
├── Controls             PlayPause, Seekbar (+ thumbnails, chapters), Volume, Time, Quality, Speed, Captions, Audio, PiP, Fullscreen, Next
├── Overlays             Skip intro/recap, next-episode countdown, buffering, error, diagnostics
├── usePlaybackTelemetry()  sends progress + QoE events
└── useKeyboardShortcuts() / useGestures()
```

Input props: `playbackUrl`, `poster`, `title`, `episode`, `startPosition`, `markers` (intro/recap/credits), `subtitleTracks`, `nextEpisode`, `onProgress`, `onEnded`.

## Features by phase

| Phase | Feature |
|---|---|
| Launch | Play/pause, seek, volume, mute, fullscreen, PiP, auto + manual quality, speed 0.5-2x, captions (WebVTT), resume, skip intro, next episode, keyboard + touch controls, error recovery |
| Next | Multiple audio tracks, chapters, seek thumbnails (sprite), subtitle styling persisted per profile, diagnostics overlay, data-saver start level |
| Later | Casting, offline (Shaka evaluation), DRM, spatial audio |

## Keyboard shortcuts

`Space`/`K` play-pause, `J`/`L` -10 s/+10 s, `←`/`→` -5 s/+5 s, `↑`/`↓` volume, `M` mute, `F` fullscreen, `C` captions, `P` PiP, `<`/`>` speed, `N` next episode, `0-9` seek to %.

## Touch gestures

Tap toggles controls, double-tap left/right seeks 10 s, long-press 2x speed (optional), swipe vertical for volume/brightness (optional).

## Adaptive streaming behavior

- Start at a conservative level (or `data_saver` level), switch up as bandwidth allows.
- Buffer target 30-60 s ahead (tune to limit wasted delivery minutes).
- Recover from network errors with limited retries; on media errors try `recoverMediaError`, then fall back to a lower level, then show an error with retry.
- Safari/iOS: use native HLS, feature-detect `canPlayType('application/vnd.apple.mpegurl')`.

## Telemetry

Progress: every 10 s while playing, on pause, on seek end, on unload (`sendBeacon`). QoE events: `start`, `first_frame` (ms), `rebuffer` (count, ms), `quality_change`, `error` (code), `end`. Batched and rate limited.

## Accessibility

All controls are buttons with labels and visible focus; slider roles with `aria-valuetext` on seek and volume; captions styleable; controls remain reachable with keyboard when auto-hidden (show on focus).

## Edge cases

Seeking beyond buffer, ended state replay, orientation change, background tab throttling, expired playback token (re-authorize silently once), autoplay blocked (show play prompt), live-region announcements for buffering and errors.

## Test plan

Unit tests for reducers and shortcut mapping; component tests with a fake engine; Playwright tests using a short local HLS fixture for play, seek, quality switch, captions, resume.
