# Frontend guide

React + TypeScript (strict) + Vite. Decision: [ADR-0004](../adr/0004-frontend-stack.md).

## Tooling

| Purpose | Tool |
|---|---|
| Build/dev | Vite |
| Styling | Tailwind CSS with design tokens ([design-system.md](design-system.md)) |
| Routing | React Router (data routers, lazy routes) |
| Server state | TanStack Query |
| Client state | Zustand (small, scoped stores) |
| Forms | react-hook-form + zod |
| API client | Generated from the backend OpenAPI schema (`openapi-typescript` + `openapi-fetch`) |
| Player | hls.js ([player-spec.md](player-spec.md)) |
| Lint/format | ESLint (typescript-eslint, react-hooks, jsx-a11y), Prettier |
| Tests | Vitest, Testing Library, Playwright, axe |
| PWA | vite-plugin-pwa (Next) |

## Project structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── public/
└── src/
    ├── main.tsx
    ├── app/                   Providers, router, layouts, error boundaries
    ├── features/              Vertical slices
    │   ├── auth/              pages, components, hooks, api
    │   ├── profiles/
    │   ├── home/
    │   ├── browse/
    │   ├── search/
    │   ├── title/
    │   ├── player/            QorvexaPlayer, controls, hooks, telemetry
    │   ├── watchlist/
    │   ├── account/
    │   └── admin/             studio: titles, uploads, analytics, moderation
    ├── components/            Shared UI primitives (Button, Dialog, Card, Skeleton...)
    ├── lib/                   api client, utils, formatters, constants
    ├── hooks/                 Shared hooks
    ├── styles/                Tailwind layers, tokens
    ├── types/                 Shared types (generated API types in types/api.ts)
    └── test/                  Test utils, MSW handlers
```

### Rules

- Features own their UI, hooks and queries; they import from `components/` and `lib/`, never from each other's internals.
- Pages are thin; logic lives in hooks and services.
- Server data only through TanStack Query hooks; no ad-hoc `fetch` in components.
- Lazy-load routes, the player and the admin studio.

## Running

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run lint && npm run typecheck && npm test
npm run build && npm run preview
```

## Environment

Only `VITE_*` variables are exposed to the browser. Never place secrets in frontend env.
