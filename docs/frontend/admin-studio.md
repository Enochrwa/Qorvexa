# Admin studio (frontend)

Code: `frontend/src/features/admin/`. Routes live under `/admin` and are loaded on demand (a separate ~8 KB gzipped chunk), so viewers never download them.

## Access

- `/admin/*` sits behind sign in (`RequireAuth`) and then `RequireEditor`. Viewers see an explanation page and the studio makes **no** admin requests for them. The header shows the "Studio" link only to editors and admins.
- This is a UI convenience. The API enforces the editor role on every admin endpoint (a backend test sweeps all of them), so hiding the screen is never the protection.

## Titles list (`/admin/titles`)

- Search by name (debounced, sent after a 300 ms pause, resets to page 1), status filter and page, all in the URL; hostile URL values are ignored. 25 per page with offset paging ("Showing 26 to 50 of 60").
- State is shown as a text badge (draft, scheduled, live, expired, archived), never colour alone.

## Title editor (`/admin/titles/new`, `/admin/titles/:id`)

- Form: name, original name, type, slug, synopsis (with counter), year, maturity rating, language, country, poster and backdrop addresses (https only), downloads flag, genres, cast and crew (billing order follows the list order).
- New titles default to the most restrictive rating (18+) with a visible reminder; lower it on purpose.
- `type` and `slug` are fixed after creation (links must keep working); the edit form shows them read-only and never sends them.
- Blank optional fields are sent as `null` so they actually clear; the same validation rules exist on the server and any server message is shown (409/422 messages are our own plain sentences; other errors use safe generic text).
- Helper text is linked with `aria-describedby`, not placed inside the label, so the field name stays short.

## Publishing panel

- Publish now, or set "Publish at" and/or "Available until" (entered in the editor's local time; converted to timezone-aware ISO before sending). A future publish time shows as `scheduled` with a "Hidden from viewers until ..." notice.
- The server refuses to publish without a synopsis and a poster (409); the reason is shown.
- Unpublish returns the title to draft. Delete is disabled while published, asks for confirmation, and returns to the list.

## Not here yet

Seasons and episodes (create, edit, reorder) are the next slice. Poster upload and media attachment arrive with Sprint 2 (Cloudinary); for now images are pasted https addresses.
