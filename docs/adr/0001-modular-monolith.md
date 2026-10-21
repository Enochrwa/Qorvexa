# ADR-0001: Modular monolith with FastAPI

- Status: Accepted
- Date: 2026-10-21

## Context

Solo developer, $0 budget, free-tier hosting with limited processes. Microservices would multiply deployment and operational cost.

## Options considered

1. Microservices: independent scaling, high operational overhead.
2. Modular monolith: one deployable, strict internal module boundaries, simple local dev.

## Decision

One FastAPI application organized by domain modules (`auth`, `catalog`, `media`, `playback`, `engagement`, `search`, `admin`), plus a separate worker process using the same codebase.

## Consequences

- Fast development and easy debugging.
- Modules talk through service interfaces, not each other's tables, so extraction is possible later.
- Must enforce boundaries with import rules and code review.
