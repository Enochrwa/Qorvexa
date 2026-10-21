# UX principles and key flows

## Principles

1. **Content first.** Posters and backdrops are the interface; chrome is minimal.
2. **Fast perceived performance.** Skeletons, optimistic updates, prefetch on hover and focus.
3. **One obvious next action.** Every title page has a primary Play/Resume button.
4. **Respect the viewer.** Clear autoplay, notification and privacy controls.
5. **Works on a phone, shines on a TV.** Large targets, focus states, remote/keyboard navigation.
6. **Accessible by default.** Captions, contrast, focus order, reduced motion.

## Key flows

### First visit to first play
Landing (public rows) -> Sign up (email + password) -> Taste picker (3+ genres, optional) -> Personalized home -> Title page -> Play.

### Watching a series
Title page shows the next unwatched episode on the Play button, season selector, episode list with progress bars, recap text hidden behind a spoiler toggle.

### Player
Controls auto-hide after 3 s; tap/click toggles play; double-tap sides seek 10 s (mobile); `Space/K` play, `J/L` seek 10 s, arrows seek 5 s / volume, `F` fullscreen, `M` mute, `C` captions, `<`/`>` speed. See [player-spec.md](../frontend/player-spec.md).

### Admin upload
Studio -> New title -> Metadata -> Upload files (drag and drop) -> per-file progress -> Processing -> Preview -> Publish or Schedule.

## Layout and states

- Mobile-first breakpoints: 360, 640, 1024, 1440, 1920.
- Every list has loading, empty, error and offline states.
- Error messages say what happened and what to do next; no raw codes shown to viewers.

## Content tone

Plain, warm, short. Avoid jargon in viewer-facing copy.

## Accessibility checklist

- Color contrast AA; do not rely on color alone.
- All player controls reachable by keyboard with visible focus.
- ARIA labels for icon buttons; live region for player status changes.
- Captions available and styleable; respect `prefers-reduced-motion`.
