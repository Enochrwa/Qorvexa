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
