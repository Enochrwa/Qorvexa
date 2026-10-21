# ADR-0008: Search with PostgreSQL full-text and trigram

- Status: Accepted
- Date: 2026-10-21

## Decision

Maintain a `search_document` `tsvector` per title (title, original title, synopsis, cast, tags) with GIN index, and `pg_trgm` indexes on title/cast for fuzzy matching. Rank by text rank plus popularity boost.

## Consequences

No extra service. If relevance or scale becomes inadequate, introduce Meilisearch or Typesense behind a `SearchService` interface.
