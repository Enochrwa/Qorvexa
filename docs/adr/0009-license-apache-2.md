# ADR-0009: Apache-2.0 license

- Status: Proposed (default chosen by the lead engineer; the owner can change it before the first release)
- Date: 2026-10-21
- Deciders: Enochrwa

## Context

The repository needs a license. The owner contributes to open source and has a $0 budget. The customer's content-rights and commercial terms are still open ([risks](../planning/risks-and-open-questions.md), questions 1 and 6).

## Options considered

1. Apache-2.0: permissive, explicit patent grant, widely accepted by companies and contributors.
2. MIT: simpler, no patent grant.
3. AGPL-3.0: protects a hosted service from closed forks, but deters contributors and customers.
4. Proprietary (all rights reserved): safest if the customer will own the code, blocks outside contributions.

## Decision

Apache-2.0. If the customer contract requires ownership or exclusivity, supersede this ADR with a proprietary license before the pilot.

## Consequences

- `LICENSE` contains the Apache-2.0 text; third-party dependencies must be compatible (avoid GPL/AGPL dependencies).
- Video content is not covered by this license and is never stored in the repository.
