"""Asset use cases: create, change status idempotently, and ingest provider events once."""

import datetime as dt
import json
import logging
import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, NotFound
from app.modules.media.models import MediaAsset, ProviderEvent
from app.modules.media.provider import AssetEvent
from app.modules.media.states import InvalidTransition, Outcome, Status, decide

log = logging.getLogger(__name__)

_MAX_PAYLOAD_BYTES = 8 * 1024


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class AssetDetails(BaseModel):
    """What a provider may fill in when an asset progresses. Anything else is ignored, so a
    provider (or a forged event that somehow passed verification) cannot set arbitrary columns."""

    model_config = ConfigDict(extra="ignore")
    duration_seconds: int | None = Field(default=None, ge=0, le=60 * 60 * 24)
    source_size_bytes: int | None = Field(default=None, ge=0)
    playback_id: str | None = Field(default=None, min_length=1, max_length=200)
    renditions: list[dict[str, Any]] | None = Field(default=None, max_length=20)
    thumbnails: dict[str, Any] | None = None


async def create_asset(
    session: AsyncSession, owner_type: str, owner_id: uuid.UUID, provider: str
) -> MediaAsset:
    asset = MediaAsset(id=uuid.uuid4(), owner_type=owner_type, owner_id=owner_id, provider=provider)
    session.add(asset)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflict("This item already has a video; delete it before uploading another") from exc
    return asset


async def _locked(session: AsyncSession, asset_id: uuid.UUID) -> MediaAsset:
    asset = await session.scalar(
        select(MediaAsset).where(MediaAsset.id == asset_id).with_for_update()
    )
    if asset is None:
        raise NotFound("Asset not found")
    return asset


async def apply_status(
    session: AsyncSession,
    asset_id: uuid.UUID,
    target: Status,
    *,
    failure_reason: str | None = None,
    details: dict[str, Any] | None = None,
) -> tuple[MediaAsset, Outcome]:
    """Move an asset to `target` if that is a legal step; a duplicate or stale request is a no-op.

    Raises InvalidTransition for the few changes that must never happen. The row is locked, so
    two concurrent calls cannot both apply.
    """
    asset = await _locked(session, asset_id)
    outcome = decide(Status(asset.status), target)
    if outcome is Outcome.APPLIED:
        asset.status = target.value
        asset.updated_at = _now()
        asset.failure_reason = (
            (failure_reason or "Unknown error")[:500] if target is Status.FAILED else None
        )
        if details:
            parsed = AssetDetails.model_validate(details)
            for key, value in parsed.model_dump(exclude_none=True).items():
                setattr(asset, key, value)
        await session.flush()
    return asset, outcome


async def retry_asset(session: AsyncSession, asset_id: uuid.UUID) -> MediaAsset:
    """Admin action: restart a failed asset from `created` (the upload is made again)."""
    asset = await _locked(session, asset_id)
    if Status(asset.status) is not Status.FAILED:
        raise Conflict("Only a failed upload can be retried")
    asset.status = Status.CREATED.value
    asset.failure_reason = None
    asset.updated_at = _now()
    await session.flush()
    return asset


class IngestResult(StrEnum):
    APPLIED = "applied"
    IGNORED = "ignored"  # stale or repeated status: nothing changed
    NO_STATUS_CHANGE = "no_status_change"
    DUPLICATE = "duplicate"  # this exact event was already processed
    UNKNOWN_ASSET = "unknown_asset"
    REJECTED = "rejected"  # inconsistent with what we know; recorded, not applied


@dataclass(frozen=True)
class Ingested:
    result: IngestResult
    asset_id: uuid.UUID | None = None


def _payload(event: AssetEvent) -> dict[str, Any]:
    body: dict[str, Any] = {
        "status": event.status.value if event.status else None,
        "provider_asset_id": event.provider_asset_id,
        "details": dict(event.details),
    }
    if len(json.dumps(body, default=str)) > _MAX_PAYLOAD_BYTES:
        return {"truncated": True, "status": body["status"]}
    return body


async def ingest_event(session: AsyncSession, event: AssetEvent) -> Ingested:
    """Process one verified provider event exactly once.

    Providers redeliver, reorder and sometimes send the same event concurrently. The unique key
    on (provider, event_id) makes the insert the gate: whoever inserts first processes, everyone
    else sees DUPLICATE. Recording the event and changing the asset share one transaction, so a
    crash in between leaves neither, and the provider's retry is processed normally.
    """
    inserted = await session.scalar(
        insert(ProviderEvent)
        .values(
            id=uuid.uuid4(),
            provider=event.provider,
            event_id=event.event_id,
            type=event.type[:80],
            payload=_payload(event),
        )
        .on_conflict_do_nothing(constraint="uq_provider_event")
        .returning(ProviderEvent.id)
    )
    if inserted is None:
        await session.commit()
        return Ingested(IngestResult.DUPLICATE)

    record = await session.get(ProviderEvent, inserted)
    assert record is not None  # noqa: S101 - just inserted in this transaction
    asset = await _find_asset(session, event)
    result, asset_id = IngestResult.UNKNOWN_ASSET, None
    if asset is not None:
        asset_id = asset.id
        result = await _apply_event(session, asset, event)
    record.processed_at = _now()
    await session.commit()
    if result is IngestResult.REJECTED:
        log.warning(
            "provider event rejected",
            extra={"extra_fields": {"provider": event.provider, "type": event.type}},
        )
    return Ingested(result, asset_id)


async def _find_asset(session: AsyncSession, event: AssetEvent) -> MediaAsset | None:
    if event.asset_id is not None:
        return await session.scalar(
            select(MediaAsset)
            .where(MediaAsset.id == event.asset_id, MediaAsset.provider == event.provider)
            .with_for_update()
        )
    if event.provider_asset_id is not None:
        return await session.scalar(
            select(MediaAsset)
            .where(
                MediaAsset.provider == event.provider,
                MediaAsset.provider_asset_id == event.provider_asset_id,
            )
            .with_for_update()
        )
    return None


async def _apply_event(session: AsyncSession, asset: MediaAsset, event: AssetEvent) -> IngestResult:
    if event.provider_asset_id:
        if asset.provider_asset_id is None:
            asset.provider_asset_id = (
                event.provider_asset_id
            )  # the first event binds the vendor's id
        elif asset.provider_asset_id != event.provider_asset_id:
            return IngestResult.REJECTED  # our id, someone else's vendor id: do not trust it
    if event.status is None:
        return IngestResult.NO_STATUS_CHANGE
    try:
        _, outcome = await apply_status(
            session,
            asset.id,
            event.status,
            failure_reason=event.failure_reason,
            details=dict(event.details),
        )
    except InvalidTransition:
        return IngestResult.REJECTED
    return IngestResult.APPLIED if outcome is Outcome.APPLIED else IngestResult.IGNORED
