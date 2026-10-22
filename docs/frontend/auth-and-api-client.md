# Auth and API client (frontend)

Code: `frontend/src/lib/api/` (client, session, errors) and `frontend/src/features/auth/`.

## Typed API client

- `src/types/api.d.ts` is generated from the backend OpenAPI schema (`make gen-api`, script `scripts/gen-api.sh`; deterministic). The CI job `api-types` fails if it is stale, so request and response shapes cannot silently drift.
- `api` (`openapi-fetch`) is the only way features call the API. `unwrap()` returns the data or throws an `ApiError` (problem+json: status, detail, `request_id`, field errors, `Retry-After`; network failures are status 0).
- `friendlyMessage()` turns errors into user text. It never shows raw server detail.

## Session and tokens

- The access token lives **in memory only** (zustand store). It is never written to localStorage, sessionStorage or cookies (tested). The refresh token is the backend's httpOnly cookie, which JavaScript cannot read.
- On page load `AuthProvider` calls `restoreSession()` once (refresh cookie, then `GET /auth/me`). Status is `loading`, `anonymous` or `authenticated`; guarded routes show a skeleton while `loading`.
- On a 401 the client refreshes and retries the request once. **All concurrent 401s share one refresh request** (`refreshSession`): refresh tokens rotate, and a second parallel request would replay a used token and trigger the backend's reuse detection, signing the user out. Verified against the real backend with 5 parallel expired requests (exactly one refresh).
- If the refresh is rejected the session is cleared; if it fails because the network is down the session is kept.
- Login, register, refresh and the email-token endpoints never trigger refresh-and-retry (no loops).
- Sign out always clears local state and the query cache, even if the request fails.

## Pages and safety rules

- Forms: react-hook-form + zod; server 422 errors are shown next to their fields; errors are `role="alert"` and linked to the field; focus moves to the first invalid field.
- Register and forgot-password show the same neutral message whatever the server knows (no account enumeration).
- `next` redirect after login is limited to same-site relative paths (`safeNext`), blocking open redirects.
- Verification and reset links carry a token: it is read once, removed from the address bar, and the page sets `Referrer-Policy: no-referrer`. Email verification is single-use, so it is requested exactly once even under React StrictMode.
- Autocomplete hints (`username`, `current-password`, `new-password`) support password managers.

## Testing

Vitest + MSW (unhandled requests fail the test) + axe-core. Colour contrast cannot be computed in jsdom; check it in a real browser. MSW cannot catch browser-only rules such as CORS preflight; those are tested on the backend (`tests/unit/test_cors.py`).

## Deployment constraint: same site for cookies

The refresh cookie is `SameSite=Lax`. Browsers do not send such cookies on cross-site `fetch` calls, so the frontend and the API must be on the **same site**. A frontend on one platform subdomain and an API on another (for example `*.pages.dev` and `*.onrender.com`) are different sites and sessions would not survive a reload. Options, to be decided in the deployment plan and **verified on the real hosts before the pilot**:

1. One custom domain with `app.` and `api.` subdomains (same site). Needs a domain: customer approval (question 9).
2. A same-origin proxy so the browser only talks to the frontend's origin (support and limits on the free tiers are not verified).
3. `SameSite=None; Secure` third-party cookies: fragile because browsers are restricting them; not recommended.
