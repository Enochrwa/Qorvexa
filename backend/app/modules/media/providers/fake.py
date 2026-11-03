"""An in-memory provider for tests and local development. It defines no vendor behaviour of its
own: it exists so the rest of the app (and the provider contract tests) have something to run."""

import hashlib
import hmac
import json
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from app.modules.media.provider import (
    AssetEvent,
    AssetRef,
    DownloadInfo,
    InvalidWebhook,
    NotPlayable,
    PlaybackContext,
    PlaybackInfo,
    UploadTicket,
)
from app.modules.media.states import Status

SIGNATURE_HEADER = "x-fake-signature"


class FakeProvider:
    name = "fake"

    def __init__(
        self,
        webhook_secret: str = "fake-webhook-secret",  # noqa: S107 - test double, not a credential
        now: datetime | None = None,
    ) -> None:
        self._secret = webhook_secret.encode()
        self._now = now
        self.deleted: list[uuid.UUID] = []

    def _clock(self) -> datetime:
        return self._now or datetime.now(UTC)

    def sign(self, body: bytes) -> str:
        """Used by tests to play the vendor: produce a valid signature."""
        return hmac.new(self._secret, body, hashlib.sha256).hexdigest()

    async def create_upload(self, asset_id: uuid.UUID, filename: str, size: int) -> UploadTicket:
        return UploadTicket(
            provider_upload_id=f"up_{asset_id.hex}",
            url=f"https://upload.fake.invalid/{asset_id.hex}",
            method="PUT",
            expires_at=self._clock() + timedelta(hours=1),
            headers={"Content-Type": "application/octet-stream"},
            part_size_bytes=8 * 1024 * 1024,
        )

    async def handle_webhook(self, headers: Mapping[str, str], body: bytes) -> AssetEvent:
        given = {k.lower(): v for k, v in headers.items()}.get(SIGNATURE_HEADER, "")
        if not given or not hmac.compare_digest(given, self.sign(body)):
            raise InvalidWebhook("bad signature")
        try:
            data = json.loads(body)
            if not isinstance(data, dict):
                raise InvalidWebhook("event must be a JSON object")
            status = Status(data["status"]) if data.get("status") else None
            return AssetEvent(
                provider=self.name,
                event_id=str(data["event_id"]),
                type=str(data["type"]),
                provider_asset_id=data.get("provider_asset_id"),
                asset_id=uuid.UUID(data["asset_id"]) if data.get("asset_id") else None,
                status=status,
                failure_reason=data.get("failure_reason"),
                details=data.get("details") or {},
            )
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise InvalidWebhook("malformed event") from exc

    async def get_playback(self, asset: AssetRef, viewer: PlaybackContext) -> PlaybackInfo:
        if asset.status != Status.READY or not asset.playback_id:
            raise NotPlayable("asset is not ready")
        return PlaybackInfo(
            url=f"https://stream.fake.invalid/{asset.playback_id}/master.m3u8",
            kind="hls",
            expires_at=self._clock() + timedelta(hours=6),
        )

    async def get_download(self, asset: AssetRef, quality: str) -> DownloadInfo | None:
        return None  # the fake offers no downloads

    async def delete(self, asset: AssetRef) -> None:
        if asset.id not in self.deleted:  # idempotent
            self.deleted.append(asset.id)
