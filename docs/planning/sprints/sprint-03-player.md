# Sprint 3: Player and playback

**Goal:** viewers play published content with a polished player; progress and resume work.
**Requirements:** FR-P1 to FR-P6, FR-P4, NFR-2
**Dates:** 2026-12-02 to 2026-12-15

## Tasks

### Backend
- [ ] `POST /playback/sessions` with publish, availability and maturity checks (M)
- [ ] Progress upsert and resume endpoints; watch history (M)
- [ ] Playback events ingestion (batched), rate limited (M)
- [ ] Next-episode selection logic (S)

### Frontend ([player-spec.md](../../frontend/player-spec.md))
- [ ] `usePlayerEngine` over hls.js with native HLS fallback (L)
- [ ] Controls: play, seek, volume, fullscreen, PiP, quality, speed, captions (XL, split)
- [ ] Keyboard shortcuts and touch gestures (M)
- [ ] Resume prompt/auto-resume; progress reporting with `sendBeacon` (M)
- [ ] Skip intro/recap and next-episode countdown (M)
- [ ] Error recovery and expired-token re-authorization (M)
- [ ] Accessibility pass on the player (M)

### Quality
- [ ] Player state unit tests; Playwright journey with local HLS fixture (L)
- [ ] Manual device matrix: Chrome, Firefox, Safari, iOS Safari, Android Chrome (M)

## Acceptance criteria

- Time to first frame p75 under 2.5 s on throttled 4G (local test harness).
- Quality adapts down under throttling without a hard stall.
- Resume lands within 5 s of the saved position across devices.
- All controls operable by keyboard; axe has no critical violations.

## Log

-

## Retro

-
