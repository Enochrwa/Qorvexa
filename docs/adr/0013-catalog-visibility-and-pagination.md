# ADR-0013: Catalog visibility rule, default audience limit and keyset pagination

- Status: Accepted (working default; maturity scale and default limit to be confirmed with the customer, see ADR-0012)
- Date: 2026-10-22
- Deciders: Enochrwa

## Context

Public catalog endpoints need a single, testable answer to "may this title be shown to this caller", and stable pagination that does not skip or repeat titles while the catalog changes.

## Decision

- **Visibility** (`app/modules/catalog/visibility.py`, used by every catalog query): `status = 'published'` AND (`publish_at` is null or in the past) AND (`available_until` is null or in the future) AND the title's rating is at or below the caller's maturity limit. `scheduled` titles stay hidden until published (by an admin or a later job). Episodes are shown only when `published`.
- **Caller limit:** the profile named by `X-Profile-Id` (must belong to the signed-in user), otherwise `PUBLIC_MATURITY_LIMIT` (default `13+`) for anonymous callers or callers without a profile.
- **Hidden looks missing:** a hidden title returns the same 404 as a nonexistent one.
- **Pagination:** keyset (cursor) on `(sort key, id)` for sorts `added` (default), `name` and `year`. Cursors are opaque base64 JSON bound to the sort they were issued for; tampered or mismatched cursors are 422. Page size 1 to 50, default 24.
- **HTTP caching:** weak ETag with `If-None-Match` support (304), `Cache-Control: private, no-cache`, `Vary: Authorization, X-Profile-Id`. Responses depend on the profile, so shared caches must not store them.
- **Abuse limit:** 120 catalog reads per minute per IP.

## Consequences

- A CDN cannot cache catalog JSON until the response is made audience-independent (for example by caching per maturity level). Revisit if traffic needs it; at pilot size it does not.
- Cursors survive inserts and deletes without skipping rows; a title whose sort key changes between pages can still appear once or be missed once, which is acceptable for browse.
- Changing the maturity scale needs a migration of `titles.maturity_rating` and `profiles.maturity_limit`.
