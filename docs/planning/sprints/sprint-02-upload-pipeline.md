# Sprint 2: Upload and processing pipeline

**Goal:** an admin can upload a video and see it become Ready, using the video provider abstraction.
**Requirements:** FR-S1, FR-S2, FR-S4 (draft/publish), NFR-3, NFR-11
**Dates:** TBD

## Tasks

### Backend
- [ ] `VideoProvider` interface and `media_assets`, `upload_sessions`, `provider_events` models ([video-pipeline.md](../../architecture/video-pipeline.md)) (L)
- [ ] `LocalProvider`: MinIO multipart presigned upload + FFmpeg HLS ladder in a worker (XL, split)
- [ ] `MuxProvider`: direct upload URL, webhook verification, state mapping (L)
- [ ] Asset state machine with idempotent transitions (M)
- [ ] ARQ worker setup; `reconcile_assets`, `cleanup_uploads` jobs (M)
- [ ] Upload endpoints: create session, complete, status, retry (M)
- [ ] `ffprobe` validation of the uploaded file (duration, codecs) (M)
- [ ] Poster and thumbnail generation (M)
- [ ] Subtitle upload (SRT -> VTT) (M)

### Frontend
- [ ] Upload studio: drag and drop, multiple files, per-file progress, pause/resume, retry (XL, split)
- [ ] Asset status chips: Uploading / Processing / Ready / Failed with reason (S)
- [ ] Preview player (basic `<video>` + hls.js) before publish (M)
- [ ] Publish / unpublish actions (S)

### Quality
- [ ] Webhook idempotency and signature tests (M)
- [ ] Resume-after-interruption test with a throttled/interrupted network (M)

## Acceptance criteria

- A 1 GB test file uploads directly to storage without increasing API memory.
- Interrupting the network mid-upload then resuming completes without restarting.
- Duplicate webhook delivery causes no duplicate state changes.
- Asset stuck in `processing` is reconciled within 10 minutes.

## Risks

FFmpeg worker needs a host with enough CPU; for the pilot prefer Mux. Time-box the self-managed path to a working local proof of concept.

## Log

-

## Retro

-
