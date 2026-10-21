# Definition of Ready and Done

## Definition of Ready (before starting an item)

- [ ] Linked to a requirement ID and has a clear user value
- [ ] Acceptance criteria written and testable
- [ ] Design/API shape sketched (endpoint, schema, or screen)
- [ ] Dependencies known; size is S, M or L (XL is split)
- [ ] Any cost impact (storage, delivery) noted

## Definition of Done (before merging)

- [ ] Code reviewed (self-review checklist when solo) and merged via PR
- [ ] Unit/integration tests added; CI green
- [ ] Types and lint pass; no new warnings
- [ ] Accessibility checked for UI changes (keyboard, labels, contrast)
- [ ] Works at 360 px width and on desktop
- [ ] Loading, empty and error states implemented
- [ ] Authorization enforced server-side and tested
- [ ] Docs updated (API/OpenAPI, schema doc, ADR if needed, sprint log)
- [ ] Migration reversible and tested (DB changes)
- [ ] No secrets, large media or debug code committed
- [ ] Performance budget not regressed (bundle size, query count)
- [ ] Telemetry/logging added where useful

## Definition of Done for a sprint

- [ ] Sprint goal met or explicitly re-scoped with reasons
- [ ] Demo recorded or shown
- [ ] Retro notes filled in; backlog re-ordered
- [ ] Staging deployed and smoke-tested
