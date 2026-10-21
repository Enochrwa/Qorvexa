# ADR-0004: Frontend stack

- Status: Accepted
- Date: 2026-10-21

## Decision

React + TypeScript (strict) + Vite, Tailwind CSS, React Router, TanStack Query for server state, Zustand for small client state, react-hook-form + zod for forms, Vitest + Testing Library + Playwright for tests. Static SPA deployed to Cloudflare Pages.

## Why

Matches existing skills, fast builds, excellent ecosystem. A static SPA is free to host and CDN-cached. SEO needs are low (login-gated catalog), but public title pages may need prerendering later (revisit if sharing previews matter).

## Consequences

- No SSR initially; Open Graph previews for shared links need a small edge function or prerender step (tracked in ideas).
- Strict TypeScript and a generated API client (OpenAPI) keep frontend and backend aligned.
