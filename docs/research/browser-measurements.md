# Real-browser measurements (2026-10-23)

Measured in headless Chromium 153 driven by Playwright, against the built frontend (`vite preview`) and the real API, Postgres, Redis and Mailpit on one machine. This is a sandbox, not production: use it for relative comparison and for catching defects, and re-measure on the real hosts before the pilot.

## 1. Page speed (Sprint 1 criterion: LCP under 2.5 s on throttled 4G)

Profile: phone viewport (412x915, 2.625 DPR), "Slow 4G" (1.6 Mbit/s down, 750 kbit/s up, 150 ms round trip) and a 4x CPU slowdown, via the DevTools protocol. 200 published titles in the catalog; the page shows the first 24. Five runs each.

| Page | LCP median (min to max) | Layout shift | Transferred |
|---|---|---|---|
| Browse, cold cache | **1956 ms** (1920 to 1992) | 0.000 | 170 KB, 8 requests |
| Browse, warm cache | 916 ms (888 to 1068) | 0.000 | 2 KB |
| Title detail, cold cache | 1796 ms (1748 to 1836) | 0.000 | 164 KB |

**Verdict:** meets the 2.5 s target with a 22% margin. No layout shift (images have reserved space). The initial JavaScript is about 161 KB gzipped (budget 200 KB); the studio is a separate lazily loaded chunk.

**What this does not cover (so do not read it as a launch guarantee):**
- Posters. The seeded titles have none (text placeholders), so LCP was text. Real posters from the video/image provider will likely become the LCP element and cost more. Use resized, `auto`-format images and re-measure.
- Real hosting. The server was on localhost. Render's free tier sleeps after 15 minutes idle and the first request then waits for a cold start (reported at about a minute; not measured by me). The first visitor after idle will blow this budget until the app shows a waking-up state or a keep-awake approach is approved.
- This machine's CPU speed is unknown, so "4x" is relative to it.

## 2. Cross-site cookies (open question Q12)

The refresh cookie is `httpOnly; SameSite=Lax`. Test: sign in, reload, see if the session survives.

| Setup | Cookie stored? | After reload |
|---|---|---|
| App `http://localhost:5173`, API `http://localhost:8000` (same site) | Yes | **Still signed in** (refresh sent the cookie, 200) |
| App `http://localhost:5174`, API `http://127.0.0.1:8000` (different sites) | **No, the browser refused it** | **Signed out** (refresh sent no cookie, 401) |

Sign-in itself works in both cases (the access token is in memory), which is what makes this easy to miss: the app looks fine until the first reload. Free platform subdomains on different hosts (for example `*.pages.dev` for the app and `*.onrender.com` for the API) are different sites, so that layout would sign every user out on every reload.

Options (not decided; see STATUS.md Q12):
1. **Serve the built frontend from the API service** (same origin, one free Render service, no CORS in production, nothing extra to buy). I can build and test this here. Trade-offs: no CDN (fine at pilot size), the first page load also waits for a cold start (as the API already does), and it changes the frontend host chosen in ADR-0010.
2. One custom domain with `app.` and `api.` subdomains (same site). Needs a domain: customer approval (question 9).
3. A same-origin proxy in front of both (Cloudflare Pages Functions or a Render rewrite). Free-tier support and limits are not verified.
4. `SameSite=None; Secure` third-party cookies: not recommended (browsers are restricting them; Safari behaviour untested here).

## 3. Colour contrast (found and fixed)

The first real-browser accessibility run failed where the jsdom tests could not see: white text on the red accent button was 3.91:1 (hover 3.16:1) and the accent as link text on raised surfaces was 4.32:1, all below the 4.5:1 WCAG AA minimum. Fixed with two tokens: `accent` (lighter, for text and links, at least 5.1:1 on every surface) and `accent-solid` (darker, for filled buttons with white text, 5.3:1, hover 6.5:1). A unit test (`frontend/tooling/contrast.test.ts`) now checks every token pair against 4.5:1, and the Playwright accessibility spec checks the rendered pages on desktop and phone viewports.
