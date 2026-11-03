import asyncio
import uuid

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, NotFound
from app.modules.media import service
from app.modules.media.models import MediaAsset, ProviderEvent
from app.modules.media.provider import AssetEvent
from app.modules.media.service import IngestResult
from app.modules.media.states import InvalidTransition, Outcome, Status

OWNER = uuid.UUID("0b1f6a52-3c0e-4a52-9b0a-1b5d9f0c1a11")


def event(
    event_id: str, status: Status | None, asset: MediaAsset | None = None, **kw: object
) -> AssetEvent:
    data: dict[str, object] = {
        "provider": "fake",
        "event_id": event_id,
        "type": "asset.updated",
        "provider_asset_id": "prov_1",
        "asset_id": asset.id if asset else None,
        "status": status,
    }
    data.update(kw)
    return AssetEvent(**data)  # type: ignore[arg-type]


async def new_asset(db: AsyncSession, owner: uuid.UUID = OWNER) -> MediaAsset:
    asset = await service.create_asset(db, "movie", owner, "fake")
    await db.commit()
    return asset


async def status_of(db: AsyncSession, asset: MediaAsset) -> str:
    await db.refresh(asset)
    return asset.status


async def test_a_new_asset_starts_as_created(db: AsyncSession) -> None:
    a = await new_asset(db)
    assert (a.status, a.provider, a.failure_reason) == ("created", "fake", None)
    assert a.renditions == [] and a.thumbnails == {}


async def test_only_one_live_asset_per_owner_but_a_deleted_one_can_be_replaced(
    db: AsyncSession,
) -> None:
    a = await new_asset(db)
    first_id = a.id  # the failed insert below rolls back and expires `a`
    with pytest.raises(Conflict):
        await service.create_asset(db, "movie", OWNER, "fake")
    await service.apply_status(db, first_id, Status.DELETED)
    await db.commit()
    b = await new_asset(db)  # allowed now
    assert b.id != first_id
    other_kind = await service.create_asset(
        db, "trailer", OWNER, "fake"
    )  # same owner, different kind
    await db.commit()
    assert other_kind.owner_type == "trailer"


async def test_status_moves_forward_and_a_repeat_changes_nothing(db: AsyncSession) -> None:
    a = await new_asset(db)
    _, first = await service.apply_status(db, a.id, Status.UPLOADED)
    await db.commit()
    stamp = a.updated_at
    _, again = await service.apply_status(db, a.id, Status.UPLOADED)
    _, late = await service.apply_status(db, a.id, Status.UPLOADING)  # stale
    await db.commit()
    assert (first, again, late) == (Outcome.APPLIED, Outcome.IGNORED, Outcome.IGNORED)
    assert await status_of(db, a) == "uploaded" and a.updated_at == stamp


async def test_ready_stores_only_the_allowed_details(db: AsyncSession) -> None:
    a = await new_asset(db)
    await service.apply_status(
        db,
        a.id,
        Status.READY,
        details={
            "duration_seconds": 2745,
            "playback_id": "pb_9",
            "renditions": [{"h": 480}],
            "status": "deleted",
            "owner_id": str(uuid.uuid4()),
            "provider": "evil",
        },
    )
    await db.commit()
    await db.refresh(a)
    assert (a.duration_seconds, a.playback_id, a.renditions, a.status) == (
        2745,
        "pb_9",
        [{"h": 480}],
        "ready",
    )
    assert a.provider == "fake" and a.owner_id == OWNER  # a provider cannot overwrite these


@pytest.mark.parametrize(
    "bad",
    [
        {"duration_seconds": -1},
        {"duration_seconds": 10**9},
        {"playback_id": ""},
        {"renditions": [{}] * 21},
    ],
)
async def test_invalid_details_are_refused_and_nothing_changes(
    db: AsyncSession, bad: dict[str, object]
) -> None:
    a = await new_asset(db)
    with pytest.raises(ValueError):
        await service.apply_status(db, a.id, Status.READY, details=bad)
    await db.rollback()
    assert await status_of(db, a) == "created"


async def test_failure_keeps_a_bounded_reason_and_clears_it_on_recovery(db: AsyncSession) -> None:
    a = await new_asset(db)
    await service.apply_status(db, a.id, Status.FAILED, failure_reason="x" * 900)
    await db.commit()
    await db.refresh(a)
    assert a.status == "failed" and a.failure_reason is not None and len(a.failure_reason) == 500
    await service.apply_status(db, a.id, Status.READY)  # the provider finished after all
    await db.commit()
    await db.refresh(a)
    assert (a.status, a.failure_reason) == ("ready", None)


async def test_a_failure_without_a_reason_still_says_something(db: AsyncSession) -> None:
    a = await new_asset(db)
    await service.apply_status(db, a.id, Status.FAILED)
    await db.commit()
    await db.refresh(a)
    assert a.failure_reason == "Unknown error"


async def test_a_ready_asset_cannot_fail_and_a_deleted_one_cannot_come_back(
    db: AsyncSession,
) -> None:
    a = await new_asset(db)
    await service.apply_status(db, a.id, Status.READY)
    with pytest.raises(InvalidTransition):
        await service.apply_status(db, a.id, Status.FAILED)
    await service.apply_status(db, a.id, Status.DELETED)
    _, outcome = await service.apply_status(db, a.id, Status.READY)
    assert outcome is Outcome.IGNORED
    await db.commit()
    assert await status_of(db, a) == "deleted"


async def test_retry_only_applies_to_failed_assets(db: AsyncSession) -> None:
    a = await new_asset(db)
    with pytest.raises(Conflict):
        await service.retry_asset(db, a.id)
    await service.apply_status(db, a.id, Status.FAILED, failure_reason="boom")
    retried = await service.retry_asset(db, a.id)
    await db.commit()
    assert (retried.status, retried.failure_reason) == ("created", None)


async def test_unknown_assets_are_not_found(db: AsyncSession) -> None:
    with pytest.raises(NotFound):
        await service.apply_status(db, uuid.uuid4(), Status.READY)


# ---- events ------------------------------------------------------------------------------


async def test_an_event_is_applied_once_and_binds_the_vendor_id(db: AsyncSession) -> None:
    a = await new_asset(db)
    out = await service.ingest_event(db, event("e1", Status.PROCESSING, a))
    assert out.result is IngestResult.APPLIED and out.asset_id == a.id
    await db.refresh(a)
    assert (a.status, a.provider_asset_id) == ("processing", "prov_1")
    rec = await db.scalar(select(ProviderEvent).where(ProviderEvent.event_id == "e1"))
    assert rec is not None and rec.processed_at is not None


async def test_redelivery_of_the_same_event_is_harmless(db: AsyncSession) -> None:
    a = await new_asset(db)
    assert (
        await service.ingest_event(db, event("e1", Status.READY, a))
    ).result is IngestResult.APPLIED
    for _ in range(3):
        assert (
            await service.ingest_event(db, event("e1", Status.READY, a))
        ).result is IngestResult.DUPLICATE
    assert await db.scalar(select(func.count()).select_from(ProviderEvent)) == 1


async def test_events_arriving_out_of_order_never_move_the_asset_backwards(
    db: AsyncSession,
) -> None:
    a = await new_asset(db)
    results = [
        (await service.ingest_event(db, event(f"e{i}", s, a))).result
        for i, s in enumerate([Status.READY, Status.PROCESSING, Status.UPLOADED])  # arrival order
    ]
    assert results == [IngestResult.APPLIED, IngestResult.IGNORED, IngestResult.IGNORED]
    assert await status_of(db, a) == "ready"


async def test_the_same_event_delivered_concurrently_is_processed_exactly_once(
    db: AsyncSession, client: object
) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.core.config import get_settings

    a = await new_asset(db)
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def deliver() -> IngestResult:
        async with maker() as s:
            return (await service.ingest_event(s, event("same", Status.READY, a))).result

    results = await asyncio.gather(*[deliver() for _ in range(6)])
    await engine.dispose()
    assert sorted(results).count(IngestResult.APPLIED) == 1
    assert results.count(IngestResult.DUPLICATE) == 5
    assert await db.scalar(select(func.count()).select_from(ProviderEvent)) == 1
    assert await status_of(db, a) == "ready"


async def test_an_event_for_an_unknown_asset_is_recorded_and_ignored(db: AsyncSession) -> None:
    out = await service.ingest_event(
        db, event("e9", Status.READY, None, provider_asset_id="never-seen")
    )
    assert out.result is IngestResult.UNKNOWN_ASSET and out.asset_id is None
    assert await db.scalar(select(func.count()).select_from(ProviderEvent)) == 1


async def test_an_event_can_find_its_asset_by_the_vendor_id(db: AsyncSession) -> None:
    a = await new_asset(db)
    await service.ingest_event(db, event("e1", Status.UPLOADING, a))  # binds prov_1
    out = await service.ingest_event(db, event("e2", Status.UPLOADED, None))  # only the vendor id
    assert out.result is IngestResult.APPLIED and out.asset_id == a.id


async def test_a_vendor_id_that_contradicts_the_binding_is_rejected(db: AsyncSession) -> None:
    a = await new_asset(db)
    await service.ingest_event(db, event("e1", Status.UPLOADING, a))
    out = await service.ingest_event(
        db, event("e2", Status.READY, a, provider_asset_id="someone-elses")
    )
    assert out.result is IngestResult.REJECTED
    assert await status_of(db, a) == "uploading"


async def test_an_event_for_another_provider_cannot_touch_the_asset(db: AsyncSession) -> None:
    a = await new_asset(db)
    out = await service.ingest_event(db, event("e1", Status.READY, a, provider="cloudinary"))
    assert out.result is IngestResult.UNKNOWN_ASSET
    assert await status_of(db, a) == "created"


async def test_an_impossible_event_is_rejected_but_recorded(db: AsyncSession) -> None:
    a = await new_asset(db)
    await service.ingest_event(db, event("e1", Status.READY, a))
    out = await service.ingest_event(db, event("e2", Status.FAILED, a))
    assert out.result is IngestResult.REJECTED
    assert await status_of(db, a) == "ready"
    assert await db.scalar(select(func.count()).select_from(ProviderEvent)) == 2


async def test_an_event_without_a_status_changes_nothing(db: AsyncSession) -> None:
    a = await new_asset(db)
    out = await service.ingest_event(db, event("e1", None, a))
    assert out.result is IngestResult.NO_STATUS_CHANGE
    assert await status_of(db, a) == "created"


async def test_oversized_payloads_are_truncated_not_stored(db: AsyncSession) -> None:
    a = await new_asset(db)
    huge = {"blob": "x" * 20_000}
    await service.ingest_event(db, event("big", Status.PROCESSING, a, details=huge))
    rec = await db.scalar(select(ProviderEvent).where(ProviderEvent.event_id == "big"))
    assert rec is not None and rec.payload.get("truncated") is True and len(str(rec.payload)) < 500


async def test_deleting_an_asset_cascades_its_upload_sessions(db: AsyncSession) -> None:
    a = await new_asset(db)
    insert = text(
        "INSERT INTO upload_sessions(id, asset_id, provider_upload_id, expires_at) "
        "VALUES (gen_random_uuid(), :a, 'u', now() + interval '1 hour')"
    )
    await db.execute(insert, {"a": a.id})
    await db.commit()
    assert await db.scalar(text("SELECT count(*) FROM upload_sessions")) == 1
    await db.execute(text("DELETE FROM media_assets WHERE id = :a"), {"a": a.id})
    await db.commit()
    assert await db.scalar(text("SELECT count(*) FROM upload_sessions")) == 0
