# Video pipeline

## Overview

Upload -> Validate -> Transcode to an adaptive ladder -> Package (HLS) -> Store -> Deliver via CDN -> Player.

## Two supported modes

| Mode | When | How |
|---|---|---|
| **Managed (Mux)** | Pilot, fastest to build | Direct upload URL, provider encodes and hosts, webhooks notify, Mux Player or hls.js plays |
| **Self-managed (R2 + FFmpeg)** | Long-term cost control | Browser uploads to R2 via multipart presigned URLs, worker runs FFmpeg, outputs HLS to R2, CDN serves |

Both implement the same interface ([ADR-0003](../adr/0003-video-provider-abstraction.md)).

## Provider interface (backend)

```python
class VideoProvider(Protocol):
    async def create_upload(self, asset_id: UUID, filename: str, size: int) -> UploadSession: ...
    async def handle_webhook(self, headers: Mapping[str, str], body: bytes) -> AssetEvent: ...
    async def get_playback(self, asset: MediaAsset, viewer: PlaybackContext) -> PlaybackInfo: ...
    async def get_download(self, asset: MediaAsset, quality: str) -> DownloadInfo | None: ...
    async def delete(self, asset: MediaAsset) -> None: ...
```

## Asset state machine

`created -> uploading -> uploaded -> processing -> ready -> published` with side exits `failed` and `deleted`. Transitions are idempotent and driven by provider webhooks, worker jobs or admin actions. A reconciliation job re-checks assets stuck in `uploading` or `processing` beyond a timeout.

## Upload requirements

- Direct to storage/provider; API never receives the file.
- Chunked, resumable, parallel parts, retry with backoff, progress in bytes.
- Client-side checks: type, extension, size cap; server-side re-validation after upload (probe with `ffprobe`).
- Optional checksum for duplicate detection.

## Encoding ladder (self-managed)

| Rendition | Resolution | Video bitrate (indicative) | Audio |
|---|---|---|---|
| 240p | 426x240 | 300 kbps | 64 kbps |
| 360p | 640x360 | 600 kbps | 96 kbps |
| 480p | 854x480 | 1000 kbps | 128 kbps |
| 720p | 1280x720 | 2500 kbps | 128 kbps |
| 1080p | 1920x1080 | 5000 kbps | 192 kbps |

Bitrates are starting points; tune per content. Cap the ladder (for example, 720p max) during the pilot to control storage and bandwidth. Use H.264 + AAC for broad compatibility, 4-6 s segments, keyframe-aligned renditions, and a master playlist.

Indicative FFmpeg per rendition (illustrative; finalize in Sprint 2):

```bash
ffmpeg -i input.mp4 -c:v libx264 -preset medium -profile:v high -g 96 -keyint_min 96 \
  -sc_threshold 0 -b:v 2500k -maxrate 2675k -bufsize 3750k -vf scale=-2:720 \
  -c:a aac -b:a 128k -hls_time 4 -hls_playlist_type vod \
  -hls_segment_filename 720p/seg_%05d.ts 720p/index.m3u8
```

## Artifacts per asset

Master playlist, rendition playlists and segments, poster and thumbnail sprites, optional downloadable MP4s, subtitle tracks (WebVTT), `ffprobe` metadata (duration, codecs, resolution).

## Subtitles and audio

WebVTT subtitles uploaded or converted from SRT; language-tagged. Alternate audio tracks packaged as separate HLS audio groups (Next).

## Delivery and access control

- Public titles: unguessable asset IDs plus short-lived signed URLs/tokens where the provider supports it.
- Restricted titles: playback authorization endpoint checks maturity limit, availability window, role, then issues a signed URL/token.
- Downloads: separate authorization, short expiry, range requests supported.

## Thumbnails and seek previews

Generate poster and a sprite sheet (one frame every 5-10 s) for seek previews; store as images served by the CDN.

## Observability

Track upload failures, processing duration, processing failures by reason, startup time, rebuffer ratio, rendition switches. See [monitoring](../devops/monitoring.md).

## Open decisions

See [ADR-0003](../adr/0003-video-provider-abstraction.md) and [risks](../planning/risks-and-open-questions.md).
