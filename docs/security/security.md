# Security

Baseline: OWASP ASVS Level 1 for the pilot; aim for Level 2 controls on auth and admin.

## Threat model (summary)

| Asset | Threats | Mitigations |
|---|---|---|
| Accounts | Credential stuffing, brute force, token theft | Argon2id, rate limits, lockout/backoff, short access tokens, rotating refresh with reuse detection, optional 2FA for admins |
| Content | Hotlinking, unauthorized downloads, link sharing | Signed/expiring playback and download URLs, authorization per request, watermark option (later), DRM (later) |
| Admin studio | Privilege escalation, malicious uploads | Server-side role checks, upload validation, isolated processing, audit log |
| API | Injection, abuse, DoS | Parameterized queries via ORM, input validation, rate limits, request size limits |
| Data | Leakage, loss | Least-privilege DB user, TLS, backups, encryption at rest by providers, PII minimization |
| Supply chain | Vulnerable dependencies | Dependabot, `pip-audit`/`npm audit`, lockfiles, CodeQL |

## Controls checklist

**Application**
- [ ] All endpoints authenticated or explicitly public; authorization tested
- [ ] Input validation with Pydantic/zod; output encoding in React
- [ ] CORS allowlist; CSRF defenses for cookie endpoints
- [ ] Security headers: CSP, HSTS, X-Content-Type-Options, Referrer-Policy, frame-ancestors
- [ ] Upload: allowlist types, size caps, probe with `ffprobe`, process in isolated worker, never execute uploaded content
- [ ] Secrets only in environment/secret manager
- [x] Audit log for admin actions (title/season/episode create, update, delete, publish, unpublish; role changes will be logged when user management lands)

**Infrastructure**
- [ ] HTTPS only; modern TLS
- [ ] Separate credentials and buckets per environment
- [ ] Bucket policies deny public listing; CORS minimal
- [ ] Backups encrypted and tested

**Process**
- [ ] Dependency updates reviewed weekly
- [ ] Incident response notes: who, how to revoke keys, how to take content down quickly
- [ ] Responsible disclosure contact (`security@` address or GitHub advisories)

## What signed URLs and DRM do and do not do

Signed URLs limit who can fetch media links and for how long; DRM adds playback protection on supported devices. Neither prevents screen capture. State this to the customer in writing.

## Secret exposure runbook

1. Revoke the exposed credential immediately at the provider.
2. Create a new credential with minimum scope; update the secret store.
3. If it reached git history, rotate anyway (history rewriting does not un-leak it), and consider cleaning history.
4. Review provider audit logs for misuse.
5. Record the incident and the fix.
