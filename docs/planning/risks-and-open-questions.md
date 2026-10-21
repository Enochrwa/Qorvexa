# Risks and open questions

## Open questions for the customer (blocking Sprint 2+)

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
