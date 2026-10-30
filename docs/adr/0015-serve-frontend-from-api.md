# ADR-0015: Serve the web app from the API service (one origin)

- Status: Accepted (engineering decision; supersedes the frontend-host part of ADR-0010; reversible, see "Alternatives")
- Date: 2026-10-23
- Deciders: Enochrwa

## Context

The session lives in an `httpOnly; SameSite=Lax` refresh cookie. Tested in a real browser (docs/research/browser-measurements.md): when the app and the API are on different sites the browser refuses to store that cookie, so every reload signs the user out. ADR-0010 put the app on Cloudflare Pages and the API on Render, which are different sites (`*.pages.dev` and `*.onrender.com`). A custom domain would fix it but costs money and needs customer approval (question 9).

## Decision

The API service also serves the built web app (`FRONTEND_DIST_DIR`, off by default). One Render free web service then hosts everything on one origin: no CORS in production, no extra service, no cost.

- `app/core/spa.py`: static files with a fallback to `index.html` for client-side routes. Real 404s for missing files and everything under `/api`. Hashed `/assets/*` are cached for a year (immutable); the HTML is `no-cache`.
- The HTML is served with a Content-Security-Policy (`script-src 'self'`, no inline scripts; images and media may come from any https host for the media provider; `frame-ancestors 'none'`), `X-Content-Type-Options`, `Referrer-Policy: no-referrer` and `X-Frame-Options: DENY`. The browser tests fail on any CSP violation.
- One Docker image builds the frontend (`VITE_API_URL=""`, meaning relative calls) and the API (`infra/docker/backend.Dockerfile`). `make serve` does the same locally.
- Developers can still run the Vite dev server against the API (different ports, same site, CORS on).

## Alternatives

- Custom domain with `app.` and `api.` subdomains: still works with this code (leave `FRONTEND_DIST_DIR` unset, host the app elsewhere) once a domain is approved.
- A same-origin proxy on a CDN: free-tier limits unverified.
- `SameSite=None` third-party cookies: fragile; rejected.

## Consequences

- No CDN for the app files at pilot size (about 160 KB gzipped per cold load, cached afterwards); revisit with real traffic. Static requests count against the host's bandwidth allowance.
- The free host's cold start now also delays the first page load, not just API calls. Needs a waking-up state (open item).
- ADR-0010's frontend host line is superseded; the Cloudflare Pages guide in deployment-free-tier.md is now the alternative path, not the plan.
- The browser e2e suite and CI run in this production shape.
