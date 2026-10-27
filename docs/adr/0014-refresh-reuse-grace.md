# ADR-0014: Short grace period for refresh-token reuse

- Status: Accepted (engineering decision; reversible with one setting; the owner should know the trade-off)
- Date: 2026-10-23
- Deciders: Enochrwa

## Context

Refresh tokens rotate on every use, and presenting an already-rotated token revokes the whole session (theft detection, ADR-0005). That is correct for theft but wrong for ordinary failures: if the server rotates the token and the response never reaches the browser (connection drops, the page is reloaded mid-request, a second tab refreshes at the same moment), the browser still holds the old token and its next, legitimate, refresh looks like theft. The user is signed out.

This was listed as a known gap since Sprint 1. It became concrete when the first CI run of the browser tests failed (a reload right after navigation), and it was reproduced deterministically in a real browser by dropping a refresh response. Two parallel refreshes with the same token also returned `[200, 401]`.

## Decision

- **Server:** a rotated token presented again is treated as a retry, not theft, only if all of these hold: it was rotated (not revoked by logout, password reset, suspension or an earlier theft detection), it was rotated at most `REFRESH_REUSE_GRACE_SECONDS` ago (default 10), and its successor has **not** been used. The retry gets a fresh token in the same session lineage; nothing else is revoked.
- Anything else is still theft: after the window, or when the successor was already used (two parties hold the lineage), the whole session is revoked.
- **Client:** if the refresh request fails because of the network (not an HTTP rejection), retry once after 400 ms.
- `REFRESH_REUSE_GRACE_SECONDS=0` restores the strict behaviour.

## Security trade-off

An attacker who steals a refresh token and presents it within 10 seconds of the legitimate rotation, before the legitimate client uses the new token, gets a valid session and is not detected. That needs the token to be stolen and used within seconds of a rotation, and any later use by the legitimate client of the successor token then reveals nothing (both lineages are valid until one is revoked). Compared with strict reuse detection this is a small, bounded weakening, chosen because signing real users out on a flaky mobile connection (the target audience) is the more frequent harm. Access tokens stay short (15 minutes) and logout, password reset and suspension still revoke everything immediately.

## Consequences

- Backend tests cover: retry succeeds, two simultaneous refreshes both succeed, replay after the window is theft, replay after the successor was used is theft even inside the window, the grace can be switched off, and tokens revoked by logout, password reset or suspension never get grace. Mutation check: with the grace disabled, the retry and two-tab tests fail.
- Browser tests (`e2e/session-resilience.spec.ts`) reproduce a lost response and quick reloads.
- A few extra valid tokens can briefly exist inside one session lineage; they all die with the lineage.
