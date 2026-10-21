# Design system

Cinematic, content-first, dark by default. Tokens are defined once (Tailwind theme + CSS variables) and reused everywhere.

## Tokens (initial proposal; finalize with the customer's branding)

| Token | Value / purpose |
|---|---|
| `--bg` | Near-black background |
| `--surface-1/2/3` | Elevated surfaces |
| `--text` / `--text-muted` | Primary and secondary text (AA contrast) |
| `--accent` | Brand accent for primary actions and focus rings |
| `--danger`, `--success`, `--warning` | Semantic colors |
| Radius | 8 / 12 / 16 px |
| Spacing | 4 px scale |
| Type | One sans family; sizes 12-48 px; line-height 1.4-1.6 |
| Motion | 150-250 ms ease-out; disabled with `prefers-reduced-motion` |

## Components (build order)

1. Primitives: Button, IconButton, Input, Select, Checkbox, Switch, Slider, Tooltip, Dialog, Menu, Tabs, Toast, Skeleton, Badge, Avatar.
2. Media components: PosterCard, BackdropHero, Row (carousel), EpisodeItem, ProgressBar, RatingStars, GenreChip.
3. Layout: AppShell, TopNav, ProfileSwitcher, Footer, AdminShell.
4. Player UI: Seekbar, VolumeControl, Menus (see [player-spec.md](player-spec.md)).

Use Radix UI primitives (or equivalent headless library) for accessible behavior; style with Tailwind.

## Patterns

- Carousels are scroll-snap with keyboard support; arrows on desktop, swipe on mobile.
- Cards show title on focus/hover and a progress bar for continue-watching.
- Skeletons match final layout to prevent layout shift.
- Empty states offer an action ("Browse titles").

## Images

Poster 2:3, backdrop 16:9, thumbnail sprite for seek. Serve AVIF/WebP at several widths; always set `width/height` to avoid CLS.

## Documentation

Storybook (Next) for primitives with a11y addon; each component documents variants, states and keyboard behavior.
