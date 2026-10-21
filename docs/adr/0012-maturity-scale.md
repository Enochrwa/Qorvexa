# ADR-0012: Age-based maturity scale

- Status: Accepted as a working default; the customer should confirm or replace it before launch
- Date: 2026-10-21
- Deciders: Enochrwa

## Context

Profiles have a maturity limit and titles will have a maturity rating (FR-A2, catalog). The docs did not define the scale. A national classification (for example the one used in Rwanda) has not been confirmed with the customer.

## Decision

Use a neutral, ordered, age-based scale: `all` < `7+` < `13+` < `16+` < `18+`. A profile may see a title when the title's rating is at or below the profile's limit. An unknown limit or rating is never allowed (fail closed).

- Default profile created at registration: `18+`. Profiles created through the API default to `13+`.
- Maximum 5 profiles per account (`MAX_PROFILES_PER_ACCOUNT`); the last profile cannot be deleted.
- Anyone logged in to the account can change a profile's limit; PIN-protected limits are an idea-backlog item.

## Consequences

- The scale lives in one place (`app/modules/profiles/maturity.py`) and in a check constraint. Replacing it later needs a migration that maps old values to new ones.
- This is a product and legal choice, not only technical: record the customer's answer in `docs/planning/risks-and-open-questions.md`.
