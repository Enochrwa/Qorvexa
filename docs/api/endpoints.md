# Endpoint catalog (v1 draft)

Auth column: `-` public, `V` viewer, `E` editor, `A` admin, `P` profile-scoped (requires `X-Profile-Id` belonging to the user: 400 if missing, 404 if not owned). All paths are served under `/api/v1`. Admin responses are `Cache-Control: no-store` and every mutation is written to `audit_log`. Catalog GETs return weak ETags (send `If-None-Match` for 304) and are limited to 120 per minute per IP. Auth endpoints return `429` (problem+json with `Retry-After`) when limits are hit; see docs/backend/auth.md. Draft; the OpenAPI spec is the source of truth once implemented.

## Auth
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /auth/register | - | Create account; always 202, even if the email exists (no enumeration) |
| POST | /auth/verify-email | - | Verify with token (204; single use) |
| POST | /auth/login | - | Access token + refresh cookie |
| POST | /auth/refresh | cookie + `X-Qorvexa-Client: web` | Rotate refresh, new access token; reuse revokes the family |
| POST | /auth/logout | V + `X-Qorvexa-Client: web` | Revoke refresh family, clear cookie (204) |
| POST | /auth/password/forgot | - | Request reset email; always 202 |
| POST | /auth/password/reset | - | Reset with token (204); signs out all sessions |
| GET | /auth/me | V | Current user (id, email, role, email_verified) |
| GET | /me | V | Current user |
| DELETE | /me | V | Delete account |

## Profiles
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | /profiles | V | List the account's profiles |
| POST | /profiles | V | Create profile (max 5 per account; 409 at the cap or on a duplicate name) |
| PATCH | /profiles/{id} | V | Partial update; unknown fields and nulls are 422; another account's profile is 404 |
| DELETE | /profiles/{id} | V | Delete profile (409 if it is the only one) |
| PUT | /profiles/{id}/taste | V | Save onboarding genres/titles |

## Catalog
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | /home | P | Home rows (continue watching, recommended, collections) |
| GET | /titles | - (optional `X-Profile-Id`) | Browse: filters `type`, `genre`, `year`, `language`; `sort=added|name|year`; `limit` 1-50; `cursor`. Only visible titles (ADR-0013) |
| GET | /titles/{slug} | - (optional `X-Profile-Id`) | Title detail with genres, cast and season count; hidden titles are 404 |
| GET | /titles/{slug}/seasons | - (optional `X-Profile-Id`) | Seasons with published episodes |
| GET | /titles/{slug}/related | - | Related titles |
| GET | /genres | - | Genre list (sorted by name) |
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
| GET/POST | /admin/titles | E | List (filters `status`, `q`, `limit`, `offset`) / create (new titles are `draft`, rating defaults to `18+`) |
| GET/PATCH/DELETE | /admin/titles/{id} | E | Manage title. `slug`, `type` and `status` cannot be patched; delete requires unpublished (409 otherwise) |
| POST | /admin/titles/{id}/publish | E | Publish; optional `publish_at` (future = embargoed, state `scheduled`) and `available_until`. 409 unless synopsis and poster exist |
| POST | /admin/titles/{id}/unpublish | E | Unpublish |
| GET/POST | /admin/titles/{id}/seasons | E | List (with all episodes) / create (series only) |
| PATCH/DELETE | /admin/seasons/{id} | E | Update / delete season |
| GET/POST | /admin/seasons/{id}/episodes | E | List / create episode |
| POST | /admin/seasons/{id}/episodes/reorder | E | Renumber episodes 1..n from an ordered id list (atomic) |
| PATCH/DELETE | /admin/episodes/{id} | E | Update (incl. `status`) / delete episode |
| POST | /admin/titles/{id}/video | E | Start a movie upload (201). Body: `filename`, `size_bytes`. Returns where the **browser** sends the file (URL, method, headers or form fields, expiry, part size). 409 for a series or if a live video exists; 413 over `MAX_UPLOAD_BYTES`; 502 if the video service is down; 503 if none is configured |
| POST | /admin/episodes/{id}/video | E | Start an episode upload (same shape) |
| GET | /admin/titles/{id}/video, /admin/episodes/{id}/video | E | The live video of that owner (404 if none) |
| GET | /admin/assets/{id} | E | Status (`created`, `uploading`, `uploaded`, `processing`, `ready`, `failed`, `deleted`), failure reason, duration, renditions |
| POST | /admin/assets/{id}/complete | E | The browser says the upload finished; moves to `uploaded`. Safe to repeat; never moves a finished asset backwards; 409 if failed or deleted |
| POST | /admin/assets/{id}/retry | E | Only for `failed` assets (409 otherwise). Body as for starting; returns a fresh upload ticket and kills the old link |
| DELETE | /admin/assets/{id} | E | Delete (204, idempotent). The asset is hidden at once even if the vendor is unreachable |
| POST | /webhooks/{provider} | - (signature) | Vendor notifications. Only the configured provider's name is accepted (else 404). Signature is verified before the body is trusted (400 if invalid or malformed); valid events are acknowledged with 200 and `{"result": "applied|ignored|duplicate|unknown_asset|rejected|no_status_change"}` so the vendor stops retrying. Bodies over 256 KB are 413; 600 per minute per address |
| POST | /admin/media/assets/{id}/subtitles | E | Add subtitle track |
| GET | /admin/analytics/overview | A | KPIs |
| GET | /admin/analytics/titles | A | Per-title stats |
| GET/PATCH | /admin/reports | A | Moderation queue |
| GET/PATCH | /admin/users | A | User management |
| POST | /webhooks/{provider} | signature | Provider events |
| GET | /health, /ready | - | Liveness, readiness |
