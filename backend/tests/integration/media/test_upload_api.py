import json
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.audit.models import AuditLog
from app.modules.media.models import MediaAsset, UploadSession
from app.modules.media.provider import AssetRef, ProviderError, UploadTicket
from app.modules.media.providers.fake import SIGNATURE_HEADER, FakeProvider
from app.modules.media.router import ServiceNotConfigured, provider_dependency
from tests.conftest import FakeEmailSender
from tests.integration.admin.helpers import A, as_role, make_title

BODY = {"filename": "film.mp4", "size_bytes": 700_000_000}


async def _movie(client: AsyncClient, h: dict[str, str]) -> str:
    return str((await make_title(client, h, name="Film", type="movie"))["id"])


async def _episode(client: AsyncClient, h: dict[str, str]) -> str:
    t = await make_title(client, h, name="Show", type="series")
    s = (await client.post(f"{A}/titles/{t['id']}/seasons", headers=h, json={"number": 1})).json()
    return str(
        (
            await client.post(
                f"{A}/seasons/{s['id']}/episodes", headers=h, json={"number": 1, "name": "Pilot"}
            )
        ).json()["id"]
    )


async def _editor(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> dict[str, str]:
    return await as_role(client, mailbox, db, "editor")


def _event(
    video: FakeProvider, event_id: str, status: str | None, asset_id: str, **extra: object
) -> tuple[dict[str, str], bytes]:
    body = json.dumps(
        {
            "event_id": event_id,
            "type": "asset.updated",
            "status": status,
            "asset_id": asset_id,
            "provider_asset_id": "prov_1",
            **extra,
        },
        sort_keys=True,
    ).encode()
    return {SIGNATURE_HEADER: video.sign(body)}, body


async def _deliver(
    client: AsyncClient,
    video: FakeProvider,
    event_id: str,
    status: str | None,
    asset_id: str,
    **extra: object,
):
    headers, body = _event(video, event_id, status, asset_id, **extra)
    return await client.post("/api/v1/webhooks/fake", headers=headers, content=body)


# ---- starting an upload ------------------------------------------------------------------


async def test_start_a_movie_upload(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    title = await _movie(client, h)
    r = await client.post(f"{A}/titles/{title}/video", headers=h, json=BODY)
    assert r.status_code == 201 and r.headers["cache-control"] == "no-store"
    t = r.json()
    assert t["provider"] == "fake" and t["method"] == "PUT" and t["url"].startswith("https://")
    assert t["part_size_bytes"] and t["expires_at"]
    asset = await db.scalar(select(MediaAsset).where(MediaAsset.id == uuid.UUID(t["asset_id"])))
    assert asset is not None and (asset.status, asset.owner_type, str(asset.owner_id)) == (
        "created",
        "movie",
        title,
    )
    sessions = list(
        await db.scalars(select(UploadSession).where(UploadSession.asset_id == asset.id))
    )
    assert (
        len(sessions) == 1 and sessions[0].state == "open" and sessions[0].uploader_id is not None
    )


async def test_the_upload_is_audited_without_the_file_name(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    await client.post(
        f"{A}/titles/{await _movie(client, h)}/video",
        headers=h,
        json={**BODY, "filename": "secret-name.mp4"},
    )
    row = await db.scalar(select(AuditLog).where(AuditLog.action == "asset.create"))
    assert (
        row is not None
        and "secret-name" not in json.dumps(row.detail)
        and row.detail["size_bytes"] == 700_000_000
    )


async def test_start_an_episode_upload(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    r = await client.post(f"{A}/episodes/{await _episode(client, h)}/video", headers=h, json=BODY)
    assert r.status_code == 201
    assert (await db.scalar(select(MediaAsset.owner_type))) == "episode"


@pytest.mark.parametrize(
    "bad",
    [
        {"filename": "film.exe", "size_bytes": 1},
        {"filename": "film", "size_bytes": 1},
        {"filename": "../etc/film.mp4", "size_bytes": 1},
        {"filename": "a\\b.mp4", "size_bytes": 1},
        {"filename": "bad\x00.mp4", "size_bytes": 1},
        {"filename": "", "size_bytes": 1},
        {"filename": "x" * 201 + ".mp4", "size_bytes": 1},
        {"filename": "film.mp4", "size_bytes": 0},
        {"filename": "film.mp4", "size_bytes": -5},
        {"filename": "film.mp4", "size_bytes": "big"},
        {"filename": "film.mp4", "size_bytes": 1, "owner_id": "x"},
        {"size_bytes": 1},
        {},
    ],
)
async def test_invalid_upload_requests_are_422(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, bad: dict[str, object]
) -> None:
    h = await _editor(client, mailbox, db)
    title = await _movie(client, h)
    assert (await client.post(f"{A}/titles/{title}/video", headers=h, json=bad)).status_code == 422
    assert await db.scalar(select(func.count()).select_from(MediaAsset)) == 0


async def test_every_allowed_extension_works_in_any_case(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    for i, name in enumerate(["a.mp4", "b.MOV", "c.mkv", "d.WebM", "e.m4v"]):
        title = (
            await _movie(client, h)
            if i == 0
            else str((await make_title(client, h, name=f"F{i}"))["id"])
        )
        assert (
            await client.post(
                f"{A}/titles/{title}/video", headers=h, json={"filename": name, "size_bytes": 5}
            )
        ).status_code == 201, name


async def test_oversized_files_are_refused_before_anything_is_created(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "1000")
    get_settings.cache_clear()
    try:
        h = await _editor(client, mailbox, db)
        title = await _movie(client, h)
        r = await client.post(
            f"{A}/titles/{title}/video", headers=h, json={"filename": "f.mp4", "size_bytes": 1001}
        )
        assert r.status_code == 413
        assert (
            await client.post(
                f"{A}/titles/{title}/video",
                headers=h,
                json={"filename": "f.mp4", "size_bytes": 1000},
            )
        ).status_code == 201
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
    assert await db.scalar(select(func.count()).select_from(MediaAsset)) == 1


async def test_owner_rules(client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession) -> None:
    h = await _editor(client, mailbox, db)
    series = await make_title(client, h, name="Show", type="series")
    assert (
        await client.post(f"{A}/titles/{series['id']}/video", headers=h, json=BODY)
    ).status_code == 409
    ghost = "00000000-0000-0000-0000-000000000000"
    assert (await client.post(f"{A}/titles/{ghost}/video", headers=h, json=BODY)).status_code == 404
    assert (
        await client.post(f"{A}/episodes/{ghost}/video", headers=h, json=BODY)
    ).status_code == 404
    assert (
        await client.post(f"{A}/titles/not-a-uuid/video", headers=h, json=BODY)
    ).status_code == 422


async def test_one_live_video_per_owner_until_it_is_deleted(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    title = await _movie(client, h)
    first = (await client.post(f"{A}/titles/{title}/video", headers=h, json=BODY)).json()
    assert (await client.post(f"{A}/titles/{title}/video", headers=h, json=BODY)).status_code == 409
    assert (await client.delete(f"{A}/assets/{first['asset_id']}", headers=h)).status_code == 204
    assert (await client.post(f"{A}/titles/{title}/video", headers=h, json=BODY)).status_code == 201


class _Broken(FakeProvider):
    async def create_upload(self, asset_id: uuid.UUID, filename: str, size: int) -> UploadTicket:
        raise ProviderError("vendor down: secret-token-123")

    async def delete(self, asset: AssetRef) -> None:
        raise ProviderError("vendor down")


async def test_a_provider_outage_is_a_clean_502_and_leaves_nothing_behind(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    title = await _movie(client, h)
    client._transport.app.dependency_overrides[provider_dependency] = lambda: _Broken()  # type: ignore[attr-defined]
    r = await client.post(f"{A}/titles/{title}/video", headers=h, json=BODY)
    assert r.status_code == 502 and "secret-token" not in r.text
    assert await db.scalar(select(func.count()).select_from(MediaAsset)) == 0
    assert await db.scalar(select(func.count()).select_from(UploadSession)) == 0


async def test_without_a_configured_provider_the_answer_is_503(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    title = await _movie(client, h)

    def missing() -> FakeProvider:
        raise ServiceNotConfigured("No video service is configured")

    client._transport.app.dependency_overrides[provider_dependency] = missing  # type: ignore[attr-defined]
    assert (await client.post(f"{A}/titles/{title}/video", headers=h, json=BODY)).status_code == 503


# ---- reading, completing, retrying, deleting -------------------------------------------------


async def test_the_video_of_an_owner_can_be_read(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    title = await _movie(client, h)
    assert (await client.get(f"{A}/titles/{title}/video", headers=h)).status_code == 404
    t = (await client.post(f"{A}/titles/{title}/video", headers=h, json=BODY)).json()
    got = (await client.get(f"{A}/titles/{title}/video", headers=h)).json()
    assert (
        got["id"] == t["asset_id"] and got["status"] == "created" and got["failure_reason"] is None
    )
    assert (await client.get(f"{A}/assets/{t['asset_id']}", headers=h)).json()["id"] == t[
        "asset_id"
    ]
    await client.delete(f"{A}/assets/{t['asset_id']}", headers=h)
    assert (await client.get(f"{A}/titles/{title}/video", headers=h)).status_code == 404


async def test_complete_moves_to_uploaded_and_can_be_repeated(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    for _ in range(3):
        r = await client.post(f"{A}/assets/{t['asset_id']}/complete", headers=h)
        assert r.status_code == 200 and r.json()["status"] == "uploaded"
    assert (
        await db.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.action == "asset.uploaded")
        )
        == 1
    )
    state = await db.scalar(select(UploadSession.state))
    assert state == "completed"


async def test_complete_never_moves_a_finished_asset_backwards(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, video: FakeProvider
) -> None:
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    assert (
        await _deliver(client, video, "e1", "ready", t["asset_id"], details={"playback_id": "pb1"})
    ).status_code == 200
    r = await client.post(f"{A}/assets/{t['asset_id']}/complete", headers=h)
    assert r.status_code == 200 and r.json()["status"] == "ready"


async def test_complete_rules(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, video: FakeProvider
) -> None:
    h = await _editor(client, mailbox, db)
    assert (await client.post(f"{A}/assets/{uuid.uuid4()}/complete", headers=h)).status_code == 404
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    await _deliver(client, video, "e1", "failed", t["asset_id"], failure_reason="bad codec")
    assert (await client.post(f"{A}/assets/{t['asset_id']}/complete", headers=h)).status_code == 409


async def test_retry_only_for_failed_and_gives_a_fresh_ticket(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, video: FakeProvider
) -> None:
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    assert (
        await client.post(f"{A}/assets/{t['asset_id']}/retry", headers=h, json=BODY)
    ).status_code == 409  # not failed
    await _deliver(client, video, "e1", "failed", t["asset_id"], failure_reason="bad codec")
    assert (await client.get(f"{A}/assets/{t['asset_id']}", headers=h)).json()[
        "failure_reason"
    ] == "bad codec"
    r = await client.post(f"{A}/assets/{t['asset_id']}/retry", headers=h, json=BODY)
    assert r.status_code == 201 and r.json()["asset_id"] == t["asset_id"]
    got = (await client.get(f"{A}/assets/{t['asset_id']}", headers=h)).json()
    assert got["status"] == "created" and got["failure_reason"] is None
    states = sorted(await db.scalars(select(UploadSession.state)))
    assert states == ["aborted", "open"]  # the old link is dead, the new one is live


async def test_a_refused_retry_changes_nothing(
    client: AsyncClient,
    mailbox: FakeEmailSender,
    db: AsyncSession,
    video: FakeProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    await _deliver(client, video, "e1", "failed", t["asset_id"], failure_reason="bad codec")
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "10")
    get_settings.cache_clear()
    try:
        assert (
            await client.post(f"{A}/assets/{t['asset_id']}/retry", headers=h, json=BODY)
        ).status_code == 413
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
    assert (await client.get(f"{A}/assets/{t['asset_id']}", headers=h)).json()["status"] == "failed"


async def test_delete_is_idempotent_audited_and_tells_the_provider(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, video: FakeProvider
) -> None:
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    for _ in range(2):
        assert (await client.delete(f"{A}/assets/{t['asset_id']}", headers=h)).status_code == 204
    assert (await client.get(f"{A}/assets/{t['asset_id']}", headers=h)).json()[
        "status"
    ] == "deleted"
    assert video.deleted == [uuid.UUID(t["asset_id"])]
    assert await db.scalar(select(UploadSession.state)) == "aborted"
    assert (
        await db.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.action == "asset.delete")
        )
        == 2
    )
    assert (await client.delete(f"{A}/assets/{uuid.uuid4()}", headers=h)).status_code == 404


async def test_delete_succeeds_even_if_the_vendor_is_down(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    client._transport.app.dependency_overrides[provider_dependency] = lambda: _Broken("fake")  # type: ignore[attr-defined]
    assert (await client.delete(f"{A}/assets/{t['asset_id']}", headers=h)).status_code == 204
    assert (
        await db.scalar(select(MediaAsset.status))
    ) == "deleted"  # hidden from everyone regardless


async def test_viewers_cannot_touch_videos(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    v = await as_role(client, mailbox, db, "viewer")
    for method, path in [
        ("GET", f"{A}/assets/{t['asset_id']}"),
        ("POST", f"{A}/assets/{t['asset_id']}/complete"),
        ("DELETE", f"{A}/assets/{t['asset_id']}"),
    ]:
        assert (await client.request(method, path, headers=v)).status_code == 403, path
        assert (await client.request(method, path)).status_code == 401, path


# ---- webhooks ----------------------------------------------------------------------------


async def test_a_genuine_event_updates_the_asset_without_any_login(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, video: FakeProvider
) -> None:
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    client.cookies.clear()
    r = await _deliver(
        client,
        video,
        "e1",
        "ready",
        t["asset_id"],
        details={"duration_seconds": 2745, "playback_id": "pb_9"},
    )
    assert (
        r.status_code == 200 and r.json() == {"result": "applied"} and "set-cookie" not in r.headers
    )
    got = (await client.get(f"{A}/assets/{t['asset_id']}", headers=h)).json()
    assert (got["status"], got["duration_seconds"]) == ("ready", 2745)


async def test_redelivery_is_acknowledged_but_not_reapplied(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, video: FakeProvider
) -> None:
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    assert (await _deliver(client, video, "e1", "processing", t["asset_id"])).json()[
        "result"
    ] == "applied"
    assert (await _deliver(client, video, "e1", "processing", t["asset_id"])).json()[
        "result"
    ] == "duplicate"
    assert (await _deliver(client, video, "e2", "uploaded", t["asset_id"])).json()[
        "result"
    ] == "ignored"  # stale


async def test_forged_events_are_refused_and_change_nothing(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, video: FakeProvider
) -> None:
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    headers, body = _event(video, "e1", "ready", t["asset_id"])
    for bad_headers, bad_body in [
        ({}, body),
        ({SIGNATURE_HEADER: "0" * 64}, body),
        (headers, body.replace(b"ready", b"deleted")),
        (headers, b""),
    ]:
        r = await client.post("/api/v1/webhooks/fake", headers=bad_headers, content=bad_body)
        assert r.status_code == 400, (bad_headers, bad_body)
    assert (await client.get(f"{A}/assets/{t['asset_id']}", headers=h)).json()[
        "status"
    ] == "created"


async def test_a_signed_but_malformed_event_is_a_clean_400(
    client: AsyncClient, video: FakeProvider
) -> None:
    for raw in (b"[]", b"null", b"not json", b'{"event_id": 5}'):
        r = await client.post(
            "/api/v1/webhooks/fake", headers={SIGNATURE_HEADER: video.sign(raw)}, content=raw
        )
        assert r.status_code == 400 and r.headers["content-type"].startswith(
            "application/problem+json"
        )


async def test_only_the_configured_provider_has_a_webhook(
    client: AsyncClient, video: FakeProvider
) -> None:
    headers, body = _event(video, "e1", "ready", str(uuid.uuid4()))
    assert (
        await client.post("/api/v1/webhooks/cloudinary", headers=headers, content=body)
    ).status_code == 404


async def test_events_for_unknown_assets_and_impossible_changes_are_acknowledged(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, video: FakeProvider
) -> None:
    assert (await _deliver(client, video, "e1", "ready", str(uuid.uuid4()))).json()[
        "result"
    ] == "unknown_asset"
    h = await _editor(client, mailbox, db)
    t = (
        await client.post(f"{A}/titles/{await _movie(client, h)}/video", headers=h, json=BODY)
    ).json()
    await _deliver(client, video, "e2", "ready", t["asset_id"])
    assert (await _deliver(client, video, "e3", "failed", t["asset_id"])).json()[
        "result"
    ] == "rejected"


async def test_oversized_webhook_bodies_are_refused(
    client: AsyncClient, video: FakeProvider
) -> None:
    raw = b'{"event_id":"e1","type":"x","pad":"' + b"a" * 300_000 + b'"}'
    r = await client.post(
        "/api/v1/webhooks/fake", headers={SIGNATURE_HEADER: video.sign(raw)}, content=raw
    )
    assert r.status_code == 413


async def test_webhooks_are_rate_limited_per_address(
    client: AsyncClient, video: FakeProvider
) -> None:
    raw = b"x"
    headers = {SIGNATURE_HEADER: "0" * 64}
    for _ in range(600):
        assert (
            await client.post("/api/v1/webhooks/fake", headers=headers, content=raw)
        ).status_code == 400
    r = await client.post("/api/v1/webhooks/fake", headers=headers, content=raw)
    assert r.status_code == 429 and "retry-after" in r.headers
