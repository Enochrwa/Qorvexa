"""Starting, finishing, retrying and deleting uploads. Provider-neutral: it only uses
`VideoProvider`. The browser sends the bytes straight to the provider (never through us)."""

import logging
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import BadGateway, Conflict, NotFound, PayloadTooLarge
from app.modules.audit import service as audit
from app.modules.catalog.models import Episode, Season, Title
from app.modules.media import service
from app.modules.media.models import MediaAsset, UploadSession
from app.modules.media.provider import AssetRef, ProviderError, UploadTicket, VideoProvider
from app.modules.media.schemas import UploadRequest
from app.modules.media.states import Outcome, Status

log = logging.getLogger(__name__)


async def _check_owner(session: AsyncSession, owner_type: str, owner_id: uuid.UUID) -> None:
    if owner_type == "movie":
        title = await session.get(Title, owner_id)
        if title is None:
            raise NotFound("Title not found")
        if title.type != "movie":
            raise Conflict("Series have videos on their episodes, not on the title")
    elif owner_type == "episode":
        found = await session.scalar(
            select(Episode.id)
            .join(Season, Season.id == Episode.season_id)
            .where(Episode.id == owner_id)
        )
        if found is None:
            raise NotFound("Episode not found")
    else:  # trailers arrive later
        raise NotFound("Unsupported owner")


def _ref(asset: MediaAsset) -> AssetRef:
    return AssetRef(
        id=asset.id,
        status=Status(asset.status),
        provider_asset_id=asset.provider_asset_id,
        playback_id=asset.playback_id,
    )


async def _ticket(provider: VideoProvider, asset_id: uuid.UUID, req: UploadRequest) -> UploadTicket:
    if req.size_bytes > get_settings().max_upload_bytes:
        limit_gb = get_settings().max_upload_bytes / 1024**3
        raise PayloadTooLarge(f"Files can be at most {limit_gb:g} GB")
    try:
        return await provider.create_upload(asset_id, req.filename, req.size_bytes)
    except ProviderError as exc:
        log.error("provider could not create an upload", exc_info=exc)
        raise BadGateway("The video service is unavailable. Try again in a moment.") from exc


def _record_session(
    session: AsyncSession, asset_id: uuid.UUID, actor: uuid.UUID, ticket: UploadTicket
) -> None:
    session.add(
        UploadSession(
            id=uuid.uuid4(),
            asset_id=asset_id,
            uploader_id=actor,
            provider_upload_id=ticket.provider_upload_id,
            expires_at=ticket.expires_at,
        )
    )


async def start_upload(
    session: AsyncSession,
    provider: VideoProvider,
    actor: uuid.UUID,
    owner_type: str,
    owner_id: uuid.UUID,
    req: UploadRequest,
) -> tuple[MediaAsset, UploadTicket]:
    await _check_owner(session, owner_type, owner_id)
    asset = await service.create_asset(session, owner_type, owner_id, provider.name)
    try:
        ticket = await _ticket(provider, asset.id, req)  # nothing is saved if this fails
    except Exception:
        await session.rollback()
        raise
    _record_session(session, asset.id, actor, ticket)
    audit.record(
        session,
        actor,
        "asset.create",
        "asset",
        asset.id,
        owner_type=owner_type,
        owner_id=str(owner_id),
        size_bytes=req.size_bytes,
    )
    await session.commit()
    return asset, ticket


async def get_asset(session: AsyncSession, asset_id: uuid.UUID) -> MediaAsset:
    asset = await session.get(MediaAsset, asset_id)
    if asset is None:
        raise NotFound("Video not found")
    return asset


async def live_asset_for(session: AsyncSession, owner_type: str, owner_id: uuid.UUID) -> MediaAsset:
    asset = await session.scalar(
        select(MediaAsset).where(
            MediaAsset.owner_type == owner_type,
            MediaAsset.owner_id == owner_id,
            MediaAsset.status != Status.DELETED.value,
        )
    )
    if asset is None:
        raise NotFound("No video yet")
    return asset


async def complete_upload(
    session: AsyncSession, actor: uuid.UUID, asset_id: uuid.UUID
) -> MediaAsset:
    """The browser says the file is uploaded. The provider's webhook stays authoritative for
    everything after this; this only moves the status forward sooner. Safe to repeat."""
    asset = await get_asset(session, asset_id)
    if Status(asset.status) in (Status.FAILED, Status.DELETED):
        raise Conflict("This upload cannot be completed; start a new one")
    open_session = await session.scalar(
        select(UploadSession)
        .where(UploadSession.asset_id == asset_id, UploadSession.state.in_(("open", "completed")))
        .order_by(UploadSession.created_at.desc())
    )
    if open_session is None:
        raise Conflict("There is no upload to complete")
    open_session.state = "completed"
    _, outcome = await service.apply_status(session, asset_id, Status.UPLOADED)
    if outcome is Outcome.APPLIED:
        audit.record(session, actor, "asset.uploaded", "asset", asset_id)
    await session.commit()
    await session.refresh(asset)
    return asset


async def _abort_open_sessions(session: AsyncSession, asset_id: uuid.UUID) -> None:
    await session.execute(
        update(UploadSession)
        .where(UploadSession.asset_id == asset_id, UploadSession.state == "open")
        .values(state="aborted")
    )


async def retry_upload(
    session: AsyncSession,
    provider: VideoProvider,
    actor: uuid.UUID,
    asset_id: uuid.UUID,
    req: UploadRequest,
) -> tuple[MediaAsset, UploadTicket]:
    asset = await get_asset(session, asset_id)
    if asset.provider != provider.name:
        raise Conflict("This video belongs to a different video service")
    try:
        ticket = await _ticket(provider, asset_id, req)  # fail before changing anything
        asset = await service.retry_asset(session, asset_id)  # only a failed asset
    except Exception:
        await session.rollback()
        raise
    await _abort_open_sessions(session, asset_id)
    _record_session(session, asset_id, actor, ticket)
    audit.record(session, actor, "asset.retry", "asset", asset_id, size_bytes=req.size_bytes)
    await session.commit()
    return asset, ticket


async def delete_asset(
    session: AsyncSession, provider: VideoProvider, actor: uuid.UUID, asset_id: uuid.UUID
) -> None:
    asset = await get_asset(session, asset_id)
    ref = _ref(asset)
    await service.apply_status(session, asset_id, Status.DELETED)
    await _abort_open_sessions(session, asset_id)
    audit.record(session, actor, "asset.delete", "asset", asset_id)
    await session.commit()
    if asset.provider == provider.name:
        try:
            await provider.delete(ref)
        except ProviderError:
            # The asset is already hidden from everyone; a cleanup job retries the vendor side.
            log.error(
                "provider delete failed; media may need manual cleanup",
                extra={"extra_fields": {"asset_id": str(asset_id)}},
            )
