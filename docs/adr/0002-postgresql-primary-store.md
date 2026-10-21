# ADR-0002: PostgreSQL as the primary store

- Status: Accepted
- Date: 2026-10-21

## Context

The domain is relational: users, profiles, titles, seasons, episodes, assets, progress, watchlists, ratings. We need full-text search and good indexing without extra services.

## Decision

Use PostgreSQL (16+) with SQLAlchemy 2.0 async and Alembic. Use `pg_trgm` and `tsvector` for search, JSONB sparingly for flexible metadata. No video bytes in the database.

## Consequences

- Strong constraints and transactions.
- One less service than adding a search engine early.
- Free-tier database storage is small: keep high-volume events (`playback_events`) aggregated and pruned.
