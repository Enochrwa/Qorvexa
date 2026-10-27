# Architecture decision records

We record significant decisions so future contributors know the context and trade-offs. Use [template.md](template.md). Number sequentially; never delete, supersede instead.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-modular-monolith.md) | Modular monolith with FastAPI | Accepted |
| [0002](0002-postgresql-primary-store.md) | PostgreSQL as primary store | Accepted |
| [0003](0003-video-provider-abstraction.md) | Video provider abstraction (Mux pilot, R2+FFmpeg path) | Abstraction accepted; Mux spend pending approval |
| [0004](0004-frontend-stack.md) | React + TypeScript + Vite + Tailwind + TanStack Query | Accepted |
| [0005](0005-auth-strategy.md) | JWT access + rotating refresh cookie, Argon2 | Accepted |
| [0006](0006-background-jobs-arq.md) | ARQ with Redis for background jobs | Accepted |
| [0007](0007-player-hlsjs.md) | hls.js with custom React controls | Accepted |
| [0008](0008-search-postgres-fts.md) | Postgres full-text and trigram search | Accepted |
| [0009](0009-license-apache-2.md) | Apache-2.0 license | Accepted |
| [0010](0010-pilot-hosting-render-neon-redis.md) | Pilot hosting: Render, Neon, owner-managed Redis | Accepted |
| [0011](0011-cloudinary-for-pilot-video.md) | Cloudinary for pilot video, posters, thumbnails | Accepted (capacity risk documented) |
| [0012](0012-maturity-scale.md) | Age-based maturity scale | Accepted (working default) |
| [0013](0013-catalog-visibility-and-pagination.md) | Catalog visibility, default audience limit, keyset pagination | Accepted (working default) |
| [0014](0014-refresh-reuse-grace.md) | Short grace period for refresh-token reuse | Accepted |
