# CI/CD

## Pipelines (GitHub Actions)

| Workflow | Trigger | Steps |
|---|---|---|
| `ci.yml` | PR, push to `main` | Backend: ruff, mypy, migrations, pytest with Postgres/Redis. Frontend: lint, typecheck, unit tests, build. Docs link check |
| `deploy-staging.yml` (add in Sprint 5) | Push to `main` | Build frontend -> Cloudflare Pages; deploy API image/host; run migrations; smoke test |
| `deploy-prod.yml` (add in Sprint 6) | Tag `v*` + approval | Same as staging with production secrets |
| `e2e.yml` (add in Sprint 3) | Nightly + PR label | Playwright against a seeded stack |
| `security.yml` (add in Sprint 5) | Weekly + PR | `pip-audit`, `npm audit`, CodeQL, secret scanning |

## Rules

- `main` is protected: PR required, CI green, linear history, no force-push.
- Dependabot weekly for pip and npm and GitHub Actions.
- Build once, deploy the same artifact across environments.
- Migrations run before the new API version starts; they must be backward compatible with the previous version for one release.
- Smoke test after deploy: `/health`, `/ready`, home endpoint, one playback authorization.

## Branching and releases

Trunk-based: short-lived branches; releases tagged with SemVer; `CHANGELOG.md` generated from Conventional Commits.

## Free-tier considerations

GitHub Actions free minutes are limited for private repos; cache dependencies, cancel redundant runs (already configured), run e2e less often.

## Branch protection plan for `main` (exact settings)

Apply under Settings → Branches → Add branch ruleset (or classic rule) for `main`. **Not applied automatically**; the owner must approve first.

| Setting | Value |
|---|---|
| Require a pull request before merging | On, 0 required approvals while solo (raise to 1 when a second contributor joins) |
| Dismiss stale approvals on new commits | On |
| Require status checks to pass | On: `backend`, `frontend`, `docker`; `docs` is informational |
| Require branches to be up to date before merging | On |
| Require conversation resolution | On |
| Require linear history | On (squash or rebase merge only) |
| Block force pushes | On |
| Restrict deletions | On |
| Include administrators | On |
| Require signed commits | Optional; off for now |

Repository security settings to enable: Dependabot alerts and security updates, secret scanning and push protection, private vulnerability reporting, CodeQL default setup (free for public repos).
