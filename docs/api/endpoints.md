# Endpoint catalog (v1 draft)

Auth column: `-` public, `V` viewer, `E` editor, `A` admin, `P` profile-scoped (requires `X-Profile-Id` belonging to the user). Draft; the OpenAPI spec is the source of truth once implemented.

## Auth
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /auth/register | - | Create account |
| POST | /auth/verify-email | - | Verify with token |
| POST | /auth/login | - | Access token + refresh cookie |
| POST | /auth/refresh | cookie | Rotate refresh, new access token |
| POST | /auth/logout | V | Revoke refresh family |
| POST | /auth/password/forgot | - | Request reset email |
| POST | /auth/password/reset | - | Reset with token |
| GET | /me | V | Current user |
| DELETE | /me | V | Delete account |

## Profiles
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | /profiles | V | List profiles |
| POST | /profiles | V | Create profile |
| PATCH | /profiles/{id} | V | Update (prefs, maturity) |
| DELETE | /profiles/{id} | V | Delete profile |
| PUT | /profiles/{id}/taste | V | Save onboarding genres/titles |

## Catalog
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | /home | P | Home rows (continue watching, recommended, collections) |
| GET | /titles | - | Browse with filters |
| GET | /titles/{slug} | - | Title detail |
| GET | /titles/{slug}/seasons | - | Seasons and episodes |
| GET | /titles/{slug}/related | - | Related titles |
| GET | /genres | - | Genre list |
| GET | /collections | - | Collections |
| GET | /search?q= | - | Search titles and people |
| GET | /search/suggest?q= | - | Autocomplete |
| GET | /surprise | P | Random relevant title |

## Playback
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /playback/sessions | P | Authorize and return playback info |
| PUT | /playback/progress | P | Upsert position |
| GET | /playback/progress/{asset_id} | P | Resume position |
| POST | /playback/events | P | QoE events (batch) |
| POST | /downloads | P | Authorize download, signed URL |
| GET | /history | P | Watch history |

## Engagement
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET/PUT/DELETE | /watchlist/{title_id} | P | Manage watchlist |
| GET | /watchlist | P | List |
| PUT | /ratings/{title_id} | P | Rate/review |
| GET | /notifications | P | List |
| PATCH | /notifications/{id} | P | Mark read |
| PUT | /notification-prefs | P | Preferences |
| POST | /reports | P | Report content |

## Admin studio
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET/POST | /admin/titles | E | List/create |
| GET/PATCH/DELETE | /admin/titles/{id} | E | Manage title |
| POST | /admin/titles/{id}/publish | E | Publish or schedule |
| POST | /admin/titles/{id}/unpublish | E | Unpublish |
| CRUD | /admin/titles/{id}/seasons, /admin/seasons/{id}/episodes | E | Series structure |
| POST | /admin/media/uploads | E | Create upload session |
| POST | /admin/media/uploads/{id}/complete | E | Mark upload complete |
| GET | /admin/media/assets/{id} | E | Status and details |
| POST | /admin/media/assets/{id}/retry | E | Retry processing |
| POST | /admin/media/assets/{id}/subtitles | E | Add subtitle track |
| GET | /admin/analytics/overview | A | KPIs |
| GET | /admin/analytics/titles | A | Per-title stats |
| GET/PATCH | /admin/reports | A | Moderation queue |
| GET/PATCH | /admin/users | A | User management |
| POST | /webhooks/{provider} | signature | Provider events |
| GET | /health, /ready | - | Liveness, readiness |
