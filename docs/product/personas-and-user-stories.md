# Personas and user stories

## Personas

**Amina, casual viewer (24).** Watches on a phone over mobile data, wants quick starts, low data use and resume. Gives up if video buffers twice.

**David, binge watcher (35).** Follows drama series on laptop and TV. Wants next-episode, skip intro, watch history and a release calendar.

**Grace, content owner / admin (45).** Uploads finished episodes, edits metadata, schedules releases, checks what is watched. Not technical; needs clear status and recoverable errors.

**Eric, editor.** Maintains metadata and subtitles but cannot change users or settings.

## User stories (selected, with acceptance criteria)

### Viewing
- As Amina, I can start a title and see video within 2.5 s on 4G so I do not give up.
  - AC: first frame p75 under 2.5 s in lab test on throttled 4G; quality adapts down instead of stalling.
- As David, when an episode ends the next one starts after a cancellable countdown.
  - AC: countdown 10 s default, can be disabled in settings; progress saved before navigation.
- As a viewer, I resume exactly where I left off on any device.
  - AC: position saved at most every 10 s and on pause/close; resume within 5 s of true position.
- As a viewer, I can change subtitle size, color and background.
  - AC: settings persist per profile; applied in fullscreen.

### Discovery
- As a new viewer, I pick a few genres and see a tailored home page immediately.
- As a viewer, I see why a title was recommended ("Because you watched ...").
- As a viewer, I can search with typos and filter by language and year.

### Downloads
- As a viewer, I can download a title only if the owner enabled downloads for it.
  - AC: download link is authorized, expires, supports range requests.

### Admin
- As Grace, I can drag in several episodes and watch each progress independently.
  - AC: interrupted uploads resume; failed processing shows a reason and a retry button.
- As Grace, I can schedule a series episode to publish next Friday at 18:00.
- As Grace, I can see the top titles, completion rates and failed uploads this week.
- As Eric, I can edit metadata but cannot see user emails or change roles.

### Safety
- As a viewer, I can report a title; the report appears in the moderation queue.
- As a parent, I can set a maturity limit on a profile and it cannot be bypassed by direct URL.
