# Sprint 5: Downloads, performance, security

**Goal:** complete Launch scope and harden for the pilot.
**Requirements:** FR-D1, NFR-1, NFR-4, NFR-5, NFR-10
**Dates:** TBD

## Tasks

### Downloads
- [ ] Download authorization endpoint with per-title flag, short-lived signed URL, range support (L)
- [ ] Download UI with quality choice (if renditions exist) and clear limits (M)
- [ ] Cost guard: per-user daily download cap (S)

### Performance
- [ ] Redis caching for public rows, ETag support, invalidation on publish (M)
- [ ] Route code-splitting audit, bundle budget check in CI (M)
- [ ] Image pipeline: responsive sizes, AVIF/WebP (M)
- [ ] DB query review with `EXPLAIN`; add missing indexes (M)
- [ ] k6 load tests for catalog, search, playback sessions (M)
- [ ] PWA app shell caching (S)

### Security and reliability
- [ ] Security headers (CSP, HSTS, etc.) on SPA and API (M)
- [ ] `security.yml`: pip-audit, npm audit, CodeQL (S)
- [ ] Audit log for admin actions (M)
- [ ] Admin 2FA (TOTP) (M, optional)
- [ ] Backup job and restore drill ([environments](../../devops/environments.md)) (M)
- [ ] Sentry integration (frontend, backend, worker) (S)
- [ ] Staging deploy workflow and smoke test (M)

## Acceptance criteria

- Download link expires, rejects other users, resumes via Range.
- Lighthouse performance 90+ on mobile for browse page.
- No high-severity findings from dependency and CodeQL scans.
- A database restore from backup works and is timed.

## Log

-

## Retro

-
