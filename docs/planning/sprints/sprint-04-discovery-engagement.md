# Sprint 4: Discovery and engagement

**Goal:** viewers find things fast and have reasons to return.
**Requirements:** FR-C2, FR-C3, FR-C5, FR-E1, FR-E2, FR-C7 (if time), FR-C8
**Dates:** 2026-12-16 to 2026-12-29

## Tasks

### Backend
- [ ] Search: `tsvector` + trigram indexes, ranking, suggest endpoint ([ADR-0008](../../adr/0008-search-postgres-fts.md)) (L)
- [ ] Watchlist and ratings endpoints (M)
- [ ] Taste onboarding endpoint and storage (S)
- [ ] Recommendation scoring service and `generate_recommendations` job ([overview](../../architecture/overview.md#recommendations)) (L)
- [ ] Home endpoint composing rows: continue watching, recommended, new, popular, collections (L)
- [ ] Related titles (M)
- [ ] Collections (editorial) and mood tags; surprise-me (M)

### Frontend
- [ ] Taste picker onboarding (M)
- [ ] Home rows with carousels, skeletons, prefetch (L)
- [ ] Search UI with suggestions, typo tolerance, filters (L)
- [ ] Watchlist, history and continue watching UI (M)
- [ ] Ratings UI (S)
- [ ] "Because you watched ..." explanations (S)

### Quality
- [ ] Recommendation unit tests (exclusions, diversity) (M)
- [ ] Search relevance fixture tests (M)

## Acceptance criteria

- Search returns relevant results for a one-character typo.
- Home p95 under 300 ms with warm cache and seeded 500 titles.
- New profile with no history still gets a populated home.
- Finished and over-maturity titles never appear in recommendations.

## Log

-

## Retro

-
