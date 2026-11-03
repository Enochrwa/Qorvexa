"""The behaviour every VideoProvider must have (ADR-0003).

Subclass `ProviderContract` as `TestSomething`, and provide two fixtures:
  provider   -> a configured provider that makes no real network calls
  webhook    -> a function (event_id, status, ...) -> (headers, body) that plays the vendor and
                signs the body exactly as the vendor would
A provider that passes this suite can be swapped in without the rest of the app changing.
"""

import json
import uuid
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

import pytest

from app.modules.media.provider import (
    AssetRef,
    InvalidWebhook,
    NotPlayable,
    PlaybackContext,
    VideoProvider,
)
from app.modules.media.states import Status

Webhook = Callable[..., tuple[Mapping[str, str], bytes]]


def _ref(status: Status, *, playback_id: str | None = "pb_123") -> AssetRef:
    return AssetRef(
        id=uuid.uuid4(), status=status, provider_asset_id="prov_1", playback_id=playback_id
    )


class ProviderContract:
    # ---- uploads -------------------------------------------------------------------------

    async def test_upload_ticket_is_usable_and_expires(self, provider: VideoProvider) -> None:
        ticket = await provider.create_upload(uuid.uuid4(), "film.mp4", 700_000_000)
        assert ticket.provider_upload_id
        assert ticket.url.startswith("https://")
        assert ticket.method in ("PUT", "POST")
        assert ticket.expires_at.tzinfo is not None and ticket.expires_at > datetime.now(UTC)
        if ticket.part_size_bytes is not None:
            assert ticket.part_size_bytes > 0

    async def test_each_asset_gets_its_own_upload(self, provider: VideoProvider) -> None:
        a = await provider.create_upload(uuid.uuid4(), "a.mp4", 1_000)
        b = await provider.create_upload(uuid.uuid4(), "b.mp4", 1_000)
        assert a.provider_upload_id != b.provider_upload_id
        assert a.url != b.url

    # ---- webhooks ------------------------------------------------------------------------

    async def test_a_genuine_event_is_parsed(
        self, provider: VideoProvider, webhook: Webhook
    ) -> None:
        asset_id = uuid.uuid4()
        headers, body = webhook(
            event_id="evt_1", status=Status.READY, asset_id=asset_id, provider_asset_id="prov_9"
        )
        event = await provider.handle_webhook(headers, body)
        assert event.provider == provider.name
        assert event.event_id == "evt_1"
        assert event.status is Status.READY
        assert event.asset_id == asset_id and event.provider_asset_id == "prov_9"

    async def test_header_names_are_case_insensitive(
        self, provider: VideoProvider, webhook: Webhook
    ) -> None:
        headers, body = webhook(event_id="evt_2", status=Status.PROCESSING)
        shouted = {k.upper(): v for k, v in headers.items()}
        assert (await provider.handle_webhook(shouted, body)).event_id == "evt_2"

    async def test_a_tampered_body_is_rejected(
        self, provider: VideoProvider, webhook: Webhook
    ) -> None:
        headers, body = webhook(event_id="evt_3", status=Status.READY)
        forged = body.replace(b"ready", b"failed") if b"ready" in body else body + b" "
        assert forged != body
        with pytest.raises(InvalidWebhook):
            await provider.handle_webhook(headers, forged)

    async def test_missing_or_wrong_signatures_are_rejected(
        self, provider: VideoProvider, webhook: Webhook
    ) -> None:
        headers, body = webhook(event_id="evt_4", status=Status.READY)
        with pytest.raises(InvalidWebhook):
            await provider.handle_webhook({}, body)
        with pytest.raises(InvalidWebhook):
            await provider.handle_webhook({k: "0" * len(v) for k, v in headers.items()}, body)
        with pytest.raises(InvalidWebhook):
            await provider.handle_webhook({k: "" for k in headers}, body)

    @pytest.mark.parametrize(
        "raw",
        [
            b"",
            b"not json",
            b"[]",
            b"null",
            b'"text"',
            b'{"event_id": 5}',
            b"\xff\xfe\x00",
            b"{" * 5000,
        ],
    )
    async def test_hostile_bodies_only_ever_raise_invalid_webhook(
        self, provider: VideoProvider, webhook: Webhook, raw: bytes
    ) -> None:
        """Even a correctly signed body can be garbage: the parser must fail cleanly, not crash."""
        headers, _ = webhook(event_id="evt_5", status=Status.READY, raw_body=raw)
        with pytest.raises(InvalidWebhook):
            await provider.handle_webhook(headers, raw)

    # ---- playback and downloads ------------------------------------------------------------

    @pytest.mark.parametrize("status", [s for s in Status if s is not Status.READY])
    async def test_nothing_plays_until_the_asset_is_ready(
        self, provider: VideoProvider, status: Status
    ) -> None:
        with pytest.raises(NotPlayable):
            await provider.get_playback(_ref(status), PlaybackContext(profile_id=uuid.uuid4()))

    async def test_a_ready_asset_plays_over_https_hls(self, provider: VideoProvider) -> None:
        ref = _ref(Status.READY)
        info = await provider.get_playback(ref, PlaybackContext(profile_id=uuid.uuid4()))
        assert info.kind == "hls" and info.url.startswith("https://")
        assert info.expires_at is None or info.expires_at > datetime.now(UTC)
        assert (
            str(ref.id) not in info.url
        )  # the address is built from the playback id, not our internal id

    async def test_a_ready_asset_without_a_playback_id_does_not_play(
        self, provider: VideoProvider
    ) -> None:
        with pytest.raises(NotPlayable):
            await provider.get_playback(
                _ref(Status.READY, playback_id=None), PlaybackContext(profile_id=uuid.uuid4())
            )

    async def test_downloads_are_absent_or_safe(self, provider: VideoProvider) -> None:
        info = await provider.get_download(_ref(Status.READY), "480p")
        if info is not None:
            assert info.url.startswith("https://") and info.expires_at > datetime.now(UTC)

    # ---- deleting ------------------------------------------------------------------------

    async def test_delete_can_be_repeated(self, provider: VideoProvider) -> None:
        ref = _ref(Status.READY)
        await provider.delete(ref)
        await provider.delete(ref)  # idempotent: no error the second time


def event_body(**fields: Any) -> bytes:
    """Helper for providers whose body is JSON: stable serialisation of an event."""
    return json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()
