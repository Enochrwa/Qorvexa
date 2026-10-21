# Roadmap

Solo developer, part-time alongside other commitments: plan in **two-week sprints**, assume about 20-25 focused hours per week and adjust with the actual velocity after Sprint 1. Dates start when Sprint 0 starts; fill in actual dates in each sprint file.

| Sprint | Theme | Outcome |
|---|---|---|
| [0](sprints/sprint-00-foundation.md) | Foundation | Repos, tooling, CI, local stack, design tokens, auth skeleton |
| [1](sprints/sprint-01-auth-catalog.md) | Accounts and catalog | Register/login, profiles, catalog CRUD, browse and title pages |
| [2](sprints/sprint-02-upload-pipeline.md) | Upload and processing | Admin upload studio, provider integration, asset states |
| [3](sprints/sprint-03-player.md) | Player and playback | HLS player, resume, next episode, captions, telemetry |
| [4](sprints/sprint-04-discovery-engagement.md) | Discovery and engagement | Search, home rows, watchlist, continue watching, recommendations |
| [5](sprints/sprint-05-downloads-performance-security.md) | Downloads, performance, security | Authorized downloads, caching, hardening, load tests |
| [6](sprints/sprint-06-pilot.md) | Pilot readiness | Real-device testing, legal pages, monitoring, cost report, go-live |

After Sprint 6: pilot with real users, measure, then plan "Next" features ([feature-roadmap](../product/feature-roadmap.md)).

## Milestones

| Milestone | When | Exit criteria |
|---|---|---|
| M0 Demo-ready skeleton | End of Sprint 1 | Log in, browse seeded catalog |
| M1 First video end-to-end | End of Sprint 3 | Admin uploads, publishes; viewer plays with resume |
| M2 Feature-complete MVP | End of Sprint 5 | All Launch (M) requirements met |
| M3 Pilot | End of Sprint 6 | Customer sign-off, cost estimate delivered |

## Decisions needed from the customer (blocking)

See [risks-and-open-questions.md](risks-and-open-questions.md): content ownership, launch target, library size, branding, budget after the pilot.

## Scope control

Anything not in the Launch column of the [requirements](../product/requirements.md) goes to the [backlog](backlog.md) unless it replaces something of equal size.
