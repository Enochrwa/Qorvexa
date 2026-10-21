# ADR-0005: Authentication strategy

- Status: Accepted
- Date: 2026-10-21

## Decision

- Passwords hashed with Argon2id.
- Short-lived JWT access token (15 min) held in memory by the SPA.
- Rotating refresh token in an `httpOnly`, `Secure`, `SameSite` cookie; stored hashed server-side with reuse detection.
- Role-based access (`viewer`, `editor`, `admin`) enforced server-side on every endpoint.
- Email verification and password reset via single-use, expiring tokens.

## Consequences

- Refresh cookie needs CORS and cookie configuration across the SPA and API domains; prefer same-site subdomains in production.
- Token theft impact is limited by short access TTL and rotation.
- See [backend/auth.md](../backend/auth.md).
