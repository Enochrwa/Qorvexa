# Frontend testing

| Level | Tools | Scope |
|---|---|---|
| Unit | Vitest | utils, reducers, hooks (player state, shortcut mapping) |
| Component | Vitest + Testing Library + MSW | forms, cards, menus, player with fake engine |
| Accessibility | jest-axe, Playwright + axe | core pages and the player |
| End-to-end | Playwright | critical journeys against a seeded local stack |
| Visual (optional) | Storybook + snapshot | design system |
| Performance | Lighthouse CI, bundle size check | budgets in [performance doc](../architecture/performance-and-scalability.md) |

## Critical e2e journeys

1. Register, verify (Mailpit), create profile, taste picker.
2. Browse, search with typo, open title, play, seek, change quality, resume after reload.
3. Series: play episode, auto next, skip intro.
4. Watchlist add/remove and continue watching.
5. Admin: create title, upload sample file, wait for Ready, publish, view as viewer.
6. Authorization: viewer cannot access `/studio`.

## Conventions

- Query by role/label first; `data-testid` as a last resort.
- MSW handlers mirror the OpenAPI examples; keep in `src/test/handlers`.
- Use a tiny HLS fixture (few seconds, 2 renditions) for player tests.
- Tests must not depend on network or real providers.
- Coverage guideline: 70% for features, 90% for player state logic.
