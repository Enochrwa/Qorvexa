"""The contract every video provider implements (ADR-0003, ADR-0011).

The rest of the app depends only on this module. Providers hold all knowledge of a vendor:
how an upload is authorised, how a webhook is verified, and how a playback URL is made.
Video bytes never pass through the API: `create_upload` returns where the *browser* sends them.
"""

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from app.modules.media.states import Status


class ProviderError(Exception):
    """The provider could not do what was asked (network, quota, bad configuration)."""


class InvalidWebhook(ProviderError):
    """Signature missing or wrong, or the body is not something this provider sends."""


class NotPlayable(ProviderError):
    """Playback or download was requested for an asset that is not ready."""


@dataclass(frozen=True)
class UploadTicket:
    """Where and how the browser uploads. Never contains a secret that outlives `expires_at`."""

    provider_upload_id: str
    url: str
    method: str  # "PUT" or "POST"
    expires_at: datetime
    headers: Mapping[str, str] = field(default_factory=dict)
    fields: Mapping[str, str] = field(default_factory=dict)  # multipart form fields, if any
    part_size_bytes: int | None = None  # set when the upload is chunked


@dataclass(frozen=True)
class AssetEvent:
    """A verified, parsed provider notification."""

    provider: str
    event_id: str  # unique per provider; used to ignore duplicate deliveries
    type: str
    provider_asset_id: str | None
    asset_id: uuid.UUID | None  # our id, when the provider echoes it back
    status: Status | None  # None when the event does not change the asset's status
    failure_reason: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)  # duration_seconds, renditions, ...


@dataclass(frozen=True)
class PlaybackContext:
    """Who is watching. Authorisation (maturity, availability) is decided before this is built."""

    profile_id: uuid.UUID


@dataclass(frozen=True)
class PlaybackInfo:
    url: str  # HLS manifest
    kind: str  # "hls"
    expires_at: datetime | None
    poster_url: str | None = None


@dataclass(frozen=True)
class DownloadInfo:
    url: str
    expires_at: datetime
    quality: str


@dataclass(frozen=True)
class AssetRef:
    """The few fields a provider needs about an asset (so it does not depend on the ORM)."""

    id: uuid.UUID
    status: Status
    provider_asset_id: str | None
    playback_id: str | None


class VideoProvider(Protocol):
    name: str

    async def create_upload(
        self, asset_id: uuid.UUID, filename: str, size: int
    ) -> UploadTicket: ...

    async def handle_webhook(self, headers: Mapping[str, str], body: bytes) -> AssetEvent:
        """Verify and parse. Raises InvalidWebhook; never trusts the body before verifying."""
        ...

    async def get_playback(self, asset: AssetRef, viewer: PlaybackContext) -> PlaybackInfo:
        """Raises NotPlayable unless the asset is ready."""
        ...

    async def get_download(self, asset: AssetRef, quality: str) -> DownloadInfo | None:
        """None when the provider (or asset) offers no download in that quality."""
        ...

    async def delete(self, asset: AssetRef) -> None:
        """Remove the media. Must be safe to call again (idempotent)."""
        ...
