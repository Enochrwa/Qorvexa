# Frontend coding standards

## TypeScript

- `strict: true`, `noUncheckedIndexedAccess: true`. No `any` without a justification comment; prefer `unknown` + narrowing.
- Use generated API types; do not hand-duplicate backend shapes.
- Validate untrusted input (forms, URL params, localStorage) with zod.

## React

- Function components and hooks only. Small components (<150 lines); extract hooks for logic.
- Co-locate: `Component.tsx`, `Component.test.tsx`, `use-thing.ts`.
- Memoize only with evidence; avoid premature `useMemo`/`useCallback`.
- Keys must be stable IDs, not array indexes.
- Error boundaries per route; Suspense for lazy routes with skeleton fallbacks.

## Naming and files

Components `PascalCase.tsx`; hooks `useThing.ts`; utilities `kebab-case.ts`; test IDs `data-testid` only when roles/labels are insufficient.

## Styling

Tailwind utility classes with design tokens; shared variants via `class-variance-authority`. No inline styles except dynamic values. Dark theme is the default; support `prefers-color-scheme` and reduced motion.

## Accessibility

Semantic HTML first; `jsx-a11y` lint must pass; axe checks in component and e2e tests for core flows; visible focus; no keyboard traps in dialogs or the player.

## Performance

Lazy-load heavy modules; use `srcset`/`loading="lazy"`; avoid large dependencies (check bundle impact in PRs); prefetch on intent.

## Security

No `dangerouslySetInnerHTML` without sanitization; never store tokens in localStorage (access token lives in memory); validate redirect URLs; CSP-friendly code (no inline scripts).

## Git hygiene

Conventional Commits; one change per PR; screenshots or short recordings for UI changes.
