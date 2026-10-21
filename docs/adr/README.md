# Architecture decision records

We record significant decisions so future contributors know the context and trade-offs. Use [template.md](template.md). Number sequentially; never delete, supersede instead.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-modular-monolith.md) | Modular monolith with FastAPI | Accepted |
| [0002](0002-postgresql-primary-store.md) | PostgreSQL as primary store | Accepted |
| [0003](0003-video-provider-abstraction.md) | Video provider abstraction (Mux pilot, R2+FFmpeg path) | Proposed, pending customer inputs |
| [0004](0004-frontend-stack.md) | React + TypeScript + Vite + Tailwind + TanStack Query | Accepted |
| [0005](0005-auth-strategy.md) | JWT access + rotating refresh cookie, Argon2 | Accepted |
| [0006](0006-background-jobs-arq.md) | ARQ with Redis for background jobs | Accepted |
| [0007](0007-player-hlsjs.md) | hls.js with custom React controls | Accepted |
| [0008](0008-search-postgres-fts.md) | Postgres full-text and trigram search | Accepted |
| [0009](0009-license-apache-2.md) | Apache-2.0 license | Proposed |
