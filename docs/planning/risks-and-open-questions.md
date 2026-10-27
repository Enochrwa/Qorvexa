# Risks and open questions

## Open questions for the customer (answers recorded 2026-10-21, see below)

1. Content: does the customer own or have rights to all content? Any third-party licensed titles with territory/time limits?
2. Launch target: demo only, small public pilot, or full production? Expected concurrent viewers?
3. Library size: how many hours at launch, and growth per month? (drives storage and cost)
4. Budget after the pilot: what monthly infrastructure budget is acceptable?
5. Downloads: required for all titles, or selected titles only? Quality limits?
6. Monetization: free, ads, subscription, pay-per-view? (payments are out of scope for MVP)
7. Branding: name, logo, colors, languages (UI and subtitles)?
8. Target audience and geography (affects bandwidth assumptions, legal obligations, payment methods)?
9. Domain: will the customer buy a custom domain?
10. Who administers content day to day, and how many admins/editors?

## Answers (recorded 2026-10-21, supplied by the project owner as proposed answers; customer to confirm)

1. Content: the customer confirms ownership or distribution rights for every title, including any territory or time limits.
2. Launch target: small public pilot, tens to low hundreds of viewers; concurrent usage tested before scaling.
3. Library size: a small set of movies and drama episodes, expanded as storage and bandwidth allow.
4. Budget: free tiers first. A sustainable monthly infrastructure budget must be agreed before public scaling.
5. Downloads: selected authorized titles only, with quality options and data-saving limits.
6. Monetization: free for the MVP. Ads, subscriptions and pay-per-view are later phases.
7. Branding: name, logo and colors pending. English UI first; a local language after confirmation.
8. Audience: Rwanda first, then wider East Africa; mobile-first, low data use.
9. Domain: free deployment URL first; a custom domain only if the customer approves the cost.
10. Administration: one primary administrator; restricted editor accounts if needed.

Working assumptions confirmed: customer-owned or authorized content, East African mobile audience, limited pilot traffic and library, English UI first (Kinyarwanda and other subtitle languages to be evaluated), public launch depends on cost, rights and customer approval.

Still unconfirmed by the customer: content rights (R4), post-pilot budget (R1).

## Risk register

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | $0 budget cannot sustain real library/traffic | High | High | Set expectations in writing; pilot caps; cost report; provider abstraction | Dev |
| R2 | Free-tier limits change or are exceeded unexpectedly | Medium | High | Verify limits per sprint; usage alerts; keep portability | Dev |
| R3 | Free API/DB hosts cold-start or lose data | High | Medium | Health UX, external backups, restore drills | Dev |
| R4 | Copyright claims on uploaded content | Medium | High | Rights record per title, takedown process, owner attestation | Customer |
| R5 | Playback fails on some devices/browsers | Medium | High | hls.js + native fallback, device matrix, H.264/AAC baseline | Dev |
| R6 | Solo developer capacity | High | Medium | Strict scope, phased roadmap, defer Next/Later | Dev |
| R7 | Self-managed transcoding too heavy for free infrastructure | High | Medium | Use managed provider for pilot; time-box FFmpeg PoC | Dev |
| R8 | Security incident (credential leak, admin takeover) | Low | High | Secret hygiene, 2FA for admins, rate limits, audit log | Dev |
| R9 | Mobile data costs deter users | Medium | Medium | Data-saver mode, capped ladder, low start level | Dev |
| R10 | Scope creep from "all features" expectation | High | Medium | Written scope, Launch/Next/Later, change control | Dev + Customer |

## Assumptions

- Content is licensed or owned by the customer.
- Audience is mainly on mobile networks in East Africa.
- Pilot size is small (tens to low hundreds of viewers).
- English plus at least one local language for UI/subtitles (to confirm).

Maturity scale (ADR-0012) is a working default; the customer should confirm it or give the classification to use before launch.

Hosting constraint (confirmed in a real browser 2026-10-23): the session cookie only works if the frontend and API are on the same site, so free platform subdomains on different hosts break sign-in persistence on every reload. A custom domain (question 9) or a verified same-origin proxy is needed before the pilot. See docs/frontend/auth-and-api-client.md.
