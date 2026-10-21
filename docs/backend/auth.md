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
