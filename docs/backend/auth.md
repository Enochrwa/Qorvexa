# Authentication and authorization

Decision: [ADR-0005](../adr/0005-auth-strategy.md).

## Token model

| Token | Lifetime | Storage | Notes |
|---|---|---|---|
| Access (JWT) | 15 min | SPA memory | Claims: `sub`, `role`, `iat`, `exp`, `jti` |
| Refresh (opaque) | 30 days, rotating | `httpOnly` `Secure` `SameSite=Lax` cookie; SHA-256 hash in DB | Reuse of a rotated token revokes the whole token family |
| Email verify / reset | 1-24 h, single use | DB hash | Rate limited |

## Flows

- **Register:** validate, hash with Argon2id, create user + default profile, send verification email.
- **Login:** constant-time compare, lockout/backoff after repeated failures, issue access + refresh.
- **Refresh:** rotate refresh token, return new access token; detect reuse.
- **Logout:** revoke refresh family; clear cookie.
- **Password reset:** always respond 202 regardless of account existence.

## Roles and permissions

| Role | Capabilities |
|---|---|
| viewer | Browse, play, profiles, watchlist, ratings, reports |
| editor | Viewer + manage catalog metadata, subtitles, uploads (no user or settings management) |
| admin | Editor + users, roles, settings, analytics, moderation |

Enforce with dependencies such as `require_role("editor")`. Profile-scoped data checks that the profile belongs to the authenticated account.

## Maturity and availability enforcement

Playback authorization checks: title published, within availability window, profile maturity limit allows the title rating, region rules if configured.

## Hardening

- Rate limit `/auth/*` by IP and identifier.
- CSRF: refresh and logout endpoints require the cookie plus a custom header; CORS restricted to known origins.
- Password policy: minimum length 10, check against common-password list; no composition rules.
- Optional later: TOTP 2FA for admins, social login.

## Implementation notes (Sprint 1)

- Code: `backend/app/modules/auth/` (`security.py` pure helpers, `service.py` use cases, `deps.py` current user and `require_role`, `router.py` HTTP).
- The role and account status are read from the database on every request, not from the JWT, so a demoted or suspended user loses access immediately. The `role` claim is informational.
- Registration and forgot-password always return 202 and do the same work, so the API does not reveal which emails have accounts. Login returns one 401 for unknown user and wrong password.
- Login for an unverified email returns 403. A completed password reset also marks the email verified (the link proved mailbox control) and signs out all sessions.
- Cookie-authenticated endpoints (`/auth/refresh`, `/auth/logout`) require the header `X-Qorvexa-Client: web` in addition to the cookie. Cookie: `httpOnly`, `SameSite=Lax`, path `/api/v1/auth`, `Secure` when `COOKIE_SECURE=true` (required in production).
- In `APP_ENV=production` the app refuses to start with the default or short `JWT_SECRET`.
- Password deny-list is a small built-in set; replace with a larger list before the pilot.
- Registration also creates a default profile (`18+`) in the same transaction. Profile-scoped endpoints use `require_profile` (`app/modules/profiles/deps.py`).
- Known gaps: two browser tabs refreshing the same token at the same instant can trip reuse detection and sign the user out.

## Rate limiting and lockout

Code: `app/core/ratelimit.py` (limiter), `app/modules/auth/throttle.py` (the numbers). Fixed windows on Redis (atomic Lua script); keys hold a SHA-256 of the email, never the address.

| Endpoint | Limit |
|---|---|
| register | 5 per hour per IP (429) |
| verify-email | 20 per hour per IP |
| login | 20 attempts per 15 min per IP; lockout after 5 failures per email+IP for 15 min; 30 failures per hour per email across all IPs |
| refresh | 120 per hour per IP |
| forgot password | 5 per hour per IP (429); max 3 emails per address per hour, extra requests still return 202 and send nothing |
| reset password | 10 per hour per IP |

- Failures are counted whether or not the account exists, so a lockout reveals nothing. A locked login is rejected even with the correct password until the window ends; a successful login clears the email+IP counter. Responses are problem+json 429 with `Retry-After`.
- Lockout is per email+IP so an attacker cannot easily lock out a victim from everywhere; the per-email cap (30 per hour) still bounds distributed guessing.
- **If Redis is unreachable** the limiter falls back to per-process memory for 10-second back-off periods and logs a warning. Limits stay on but are not shared across instances. It never disables limiting and never blocks all logins.
- Client IP: `X-Forwarded-For` is ignored unless `TRUSTED_PROXY_COUNT` is set; then the entry added by the outermost trusted proxy is used (not the spoofable left side). On Render set `TRUSTED_PROXY_COUNT=1` after confirming how Render appends the header; otherwise all users behind the proxy would share one IP bucket.
