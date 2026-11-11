import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.core.errors import DomainError, NotFound, PayloadTooLarge
from app.core.ratelimit import Limiter, client_ip, get_rate_limiter
from app.modules.auth.deps import CurrentUser, require_role
from app.modules.media import service, upload_service
from app.modules.media.provider import InvalidWebhook, UploadTicket, VideoProvider
from app.modules.media.registry import ProviderNotConfigured, get_video_provider
from app.modules.media.schemas import AssetOut, UploadRequest, UploadTicketOut, WebhookAck

log = logging.getLogger(__name__)


class ServiceNotConfigured(DomainError):
    status = 503
    title = "Video service not configured"


def provider_dependency() -> VideoProvider:
    try:
        return get_video_provider()
    except ProviderNotConfigured as exc:
        raise ServiceNotConfigured("No video service is configured") from exc


async def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


Session = Annotated[AsyncSession, Depends(get_session)]
Provider = Annotated[VideoProvider, Depends(provider_dependency)]
Editor = Annotated[CurrentUser, Depends(require_role("editor"))]

admin_router = APIRouter(prefix="/admin", tags=["media"], dependencies=[Depends(_no_store)])
webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _ticket_out(asset_id: uuid.UUID, provider: str, t: UploadTicket) -> UploadTicketOut:
    return UploadTicketOut(
        asset_id=asset_id,
        provider=provider,
        url=t.url,
        method=t.method,
        headers=dict(t.headers),
        fields=dict(t.fields),
        expires_at=t.expires_at,
        part_size_bytes=t.part_size_bytes,
    )


async def _start(
    owner_type: str,
    owner_id: uuid.UUID,
    body: UploadRequest,
    user: CurrentUser,
    session: AsyncSession,
    provider: VideoProvider,
) -> UploadTicketOut:
    asset, ticket = await upload_service.start_upload(
        session, provider, user.id, owner_type, owner_id, body
    )
    return _ticket_out(asset.id, provider.name, ticket)


@admin_router.post("/titles/{title_id}/video", status_code=201)
async def start_movie_upload(
    title_id: uuid.UUID, body: UploadRequest, user: Editor, session: Session, provider: Provider
) -> UploadTicketOut:
    return await _start("movie", title_id, body, user, session, provider)


@admin_router.post("/episodes/{episode_id}/video", status_code=201)
async def start_episode_upload(
    episode_id: uuid.UUID, body: UploadRequest, user: Editor, session: Session, provider: Provider
) -> UploadTicketOut:
    return await _start("episode", episode_id, body, user, session, provider)


@admin_router.get("/titles/{title_id}/video")
async def get_movie_video(title_id: uuid.UUID, _: Editor, session: Session) -> AssetOut:
    return AssetOut.model_validate(await upload_service.live_asset_for(session, "movie", title_id))


@admin_router.get("/episodes/{episode_id}/video")
async def get_episode_video(episode_id: uuid.UUID, _: Editor, session: Session) -> AssetOut:
    return AssetOut.model_validate(
        await upload_service.live_asset_for(session, "episode", episode_id)
    )


@admin_router.get("/assets/{asset_id}")
async def get_asset(asset_id: uuid.UUID, _: Editor, session: Session) -> AssetOut:
    return AssetOut.model_validate(await upload_service.get_asset(session, asset_id))


@admin_router.post("/assets/{asset_id}/complete")
async def complete_upload(asset_id: uuid.UUID, user: Editor, session: Session) -> AssetOut:
    return AssetOut.model_validate(await upload_service.complete_upload(session, user.id, asset_id))


@admin_router.post("/assets/{asset_id}/retry", status_code=201)
async def retry_upload(
    asset_id: uuid.UUID, body: UploadRequest, user: Editor, session: Session, provider: Provider
) -> UploadTicketOut:
    asset, ticket = await upload_service.retry_upload(session, provider, user.id, asset_id, body)
    return _ticket_out(asset.id, provider.name, ticket)


@admin_router.delete("/assets/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: uuid.UUID, user: Editor, session: Session, provider: Provider
) -> None:
    await upload_service.delete_asset(session, provider, user.id, asset_id)


WEBHOOKS_PER_IP = (600, 60)


@webhook_router.post("/{provider_name}")
async def receive_webhook(
    provider_name: str,
    request: Request,
    session: Session,
    provider: Provider,
    limiter: Annotated[Limiter, Depends(get_rate_limiter)],
) -> WebhookAck:
    """Vendor notifications. Not signed in: authenticity comes from the provider verifying the
    signature before anything in the body is trusted. Valid but irrelevant events are
    acknowledged (200) so the vendor stops retrying; forged or malformed ones get 400."""
    if provider_name != provider.name:
        raise NotFound("Unknown webhook")
    await limiter.enforce(f"rl:webhook:{provider.name}:{client_ip(request)}", *WEBHOOKS_PER_IP)
    limit = get_settings().webhook_max_bytes
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > limit:
        raise PayloadTooLarge("Webhook body too large")
    body = await request.body()
    if len(body) > limit:
        raise PayloadTooLarge("Webhook body too large")
    try:
        event = await provider.handle_webhook(request.headers, body)
    except InvalidWebhook as exc:
        log.warning(
            "webhook rejected",
            extra={"extra_fields": {"provider": provider.name, "reason": str(exc)[:80]}},
        )
        raise DomainError("Invalid webhook") from exc
    ingested = await service.ingest_event(session, event)
    return WebhookAck(result=ingested.result.value)
