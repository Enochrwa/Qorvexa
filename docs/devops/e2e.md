# End-to-end tests

Real browser (Playwright, Chromium) against the real stack: built frontend, API, Postgres, Redis and Mailpit. Specs live in `frontend/e2e/`; they are separate from the Vitest unit tests (`npm test`).

| Spec | What it proves |
|---|---|
| `auth.spec.ts` | Sign up with an emailed link, sign in refused until verified, session survives a reload (httpOnly cookie, no JWT in browser storage), sign out ends it, wrong password message, protected pages return you after sign in, `?next` cannot leave the site, password reset by email (new password works, old one does not, other devices are signed out, link is single use) |
| `catalog.spec.ts` | Anonymous visitors get a safe default catalog; filters live in the URL; a hidden title looks like a missing one; the selected profile changes what is visible and is remembered across reload and sign in; a deleted profile does not strand the app |
| `studio.spec.ts` | Viewers cannot use the studio; an admin builds a series, reorders episodes **with the keyboard only**, publishes it and viewers see the new order; unpublish hides it; scheduled titles stay hidden |
| `session-resilience.spec.ts` | A refresh response that never reaches the browser, and rapid reloads, do not sign the user out |
| `a11y.spec.ts` | axe (WCAG 2.0/2.1 A and AA, **including colour contrast**) on public, signed-in and studio pages |

`catalog` and `a11y` also run on a phone-sized viewport (Pixel 7) because the product is mobile-first.

## Run it locally

The default is the production shape: the API serves the built web app on one origin (ADR-0015). Settings for the API (the rest are the usual `.env` values):

```
FRONTEND_DIST_DIR=../frontend/dist   # after: cd frontend && VITE_API_URL= npm run build
FRONTEND_URL=http://localhost:8000
TRUSTED_PROXY_COUNT=1                # each test presents its own client address (see below)
SMTP_HOST=localhost SMTP_PORT=1025   # Mailpit
```

```bash
docker compose up -d                       # Postgres, Redis, Mailpit
make migrate
SEED_ADMIN_EMAIL=e2e-admin@example.com SEED_ADMIN_PASSWORD='<a long random value>' make seed
(cd frontend && VITE_API_URL= npm run build)
make backend-dev                           # API and web app on http://localhost:8000
cd frontend
export E2E_BASE_URL=http://localhost:8000
export E2E_ADMIN_EMAIL=e2e-admin@example.com E2E_ADMIN_PASSWORD='<same value>'
npx playwright install chromium           # once
npm run e2e                                # or: npx playwright test --project=desktop e2e/auth.spec.ts
```

The studio specs are skipped when `E2E_ADMIN_EMAIL` and `E2E_ADMIN_PASSWORD` are not set. Use `E2E_CHROMIUM_PATH=/path/to/chromium` to use an existing Chromium instead of Playwright's download. Other overrides: `E2E_API_URL`, `MAILPIT_URL`. The old two-port development mode (Vite on 5173, API on 8000, `CORS_ORIGINS` set) still works: set `E2E_BASE_URL=http://localhost:5173`. Any Content-Security-Policy violation in the browser console fails a test.

## Why each test has its own client address

The API limits sign-ins and sign-ups per client address. One machine running the whole suite would hit those limits and fail for the wrong reason. So the test fixtures (`e2e/fixtures.ts`) add a random `X-Forwarded-For` to API requests, and the API runs with `TRUSTED_PROXY_COUNT=1` so it reads it. The header is added after the browser's CORS checks, so it does not need to be an allowed header. This also exercises the proxy-aware client address code for real. The rate limits themselves are covered by backend tests.

## Rules for writing e2e tests

- **Never reuse a saved login (Playwright `storageState`).** Refresh tokens rotate; two tests sharing one saved cookie would replay a used token, trigger reuse detection and revoke the session family. Each test signs in itself; the shared viewer is created once in `global-setup.ts`.
- Create accounts through the API (`createVerifiedUser`) unless sign up is what the test is about.
- Locate by role and accessible name; the specs double as an accessibility check on naming. Use `exact: true` when a name could be a substring of something else (a profile is named after its owner's email).
- Clean up what you create (the studio specs delete their titles).

## CI

The `e2e` job in `.github/workflows/ci.yml` starts Postgres, Redis and Mailpit as service containers, seeds with a random admin password that exists only in that job, builds the frontend (served by the API, one origin), installs Chromium and runs the suite. On failure it uploads the Playwright report, traces, screenshots and the API log. It is informational until it has proved stable; then add it to the required checks (docs/devops/ci-cd.md).
