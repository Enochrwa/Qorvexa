# State, data fetching and routing

## State categories

| Kind | Tool | Examples |
|---|---|---|
| Server state | TanStack Query | titles, home rows, progress, watchlist |
| URL state | React Router search params | filters, sort, search query, season |
| Local UI state | `useState`/`useReducer` | open menus, form inputs |
| Shared client state | Zustand | auth session (in memory), active profile, player preferences |
| Persisted prefs | localStorage (non-sensitive) + server profile | volume, subtitle style, autoplay |

## Data fetching

- Generated client from OpenAPI; wrap in query hooks (`useTitles`, `useTitle(slug)`, `useHome`).
- Query keys are structured arrays: `['titles', filters]`, `['title', slug]`, `['progress', assetId]`.
- Defaults: `staleTime` 60 s for catalog, 0 for progress; retry 2 with backoff; no retry on 4xx.
- Mutations use optimistic updates for watchlist and ratings; roll back on error.
- Prefetch title data and player chunk on hover/focus.

## Auth in the SPA

Access token stays in memory; a fetch wrapper attaches it and, on 401, calls `/auth/refresh` once (single-flight) then retries. On refresh failure, clear state and redirect to login preserving the return URL.

## Routing

```
/                    Landing or home (by auth)
/login /register /verify /forgot /reset
/profiles            Profile picker
/browse, /browse/:genre
/search
/title/:slug
/watch/:assetId      Player (lazy)
/watchlist /history /account
/studio/*            Admin (role-guarded, lazy)
```

Route guards check auth and role in loaders; server remains the source of truth.

## Errors and offline

Route-level error boundaries; global toast for network errors; offline banner; queued progress events flushed on reconnect.
