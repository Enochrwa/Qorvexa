# Contributing to Qorvexa

## Workflow

1. Pick an item from the current sprint ([docs/planning/sprints](docs/planning/sprints)).
2. Branch from `main`: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`, `chore/<short-name>`.
3. Keep PRs small and focused. Fill in the PR template.
4. CI must pass (lint, types, tests, build) before merge.
5. Squash-merge into `main`.

## Commit messages (Conventional Commits)

```
feat(player): add playback speed menu
fix(api): reject expired refresh tokens
docs(adr): record video provider decision
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `perf`.

## Definition of done

See [docs/planning/definition-of-done.md](docs/planning/definition-of-done.md).

## Code standards

- Backend: [docs/backend/coding-standards.md](docs/backend/coding-standards.md)
- Frontend: [docs/frontend/coding-standards.md](docs/frontend/coding-standards.md)

## Secrets

Never commit secrets, tokens or `.env` files. Use `.env.example` for documented variables. If a secret is exposed, revoke it immediately and rotate.

## Architecture changes

Significant decisions need an ADR in [docs/adr](docs/adr) using the template there.
