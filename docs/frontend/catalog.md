# Catalog UI (browse and title detail)

Code: `frontend/src/features/catalog/`.

## Browse (`/browse`, also the home address)

- Filters (type, genre, sort) live in the URL, so pages can be bookmarked and the back button works. The URL is treated as user input: unknown or malformed values are ignored (`parseFilters`), and defaults are left out of the URL.
- Results use the generated typed client and cursor pagination (24 per page, "Load more"). Loading shows a skeleton grid that matches the final layout; empty and error states offer "Clear filters" / "Try again".
- A failed "Load more" keeps the titles already shown and reports the error (TanStack Query marks the whole query as errored when a later page fails, so the page only shows the full error when there is no data at all).
- Posters render only over `https`, in a fixed 2:3 box with `width`/`height` and `loading="lazy"`, so images never shift the layout; a missing or broken image falls back to the title text.
- Cache keys include the selected profile, because the catalog differs per profile (maturity limit).

## Title detail (`/titles/:slug`)

- Hero (poster, optional backdrop), rating, year, type, language, genre chips linking to a filtered browse, synopsis and credits. Series show seasons (buttons with `aria-pressed`) and published episodes with runtimes.
- A hidden, expired or unknown title shows the same calm "not available" page; the slug is validated before any request.
- Playback is not built yet (Sprint 3), so there is deliberately no Play button.

## Stale profile

If the selected profile was deleted elsewhere, the API answers `404 "Profile not found"`. `withProfileRecovery` forgets it and retries once without it, so the user sees the catalog. Verified against the real backend.

## Retry policy

`shouldRetry` (`src/lib/query-client.ts`): client errors (400, 401, 403, 404, 409, 422, 429) are never retried; server and network errors are retried once.

## Typed responses

The catalog endpoints return a raw response (for ETags), so their schemas are declared with `response_model` in the router; a backend test fails if they disappear from the OpenAPI document, which would leave the frontend untyped.
