import datetime as dt
import uuid
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

_STATUSES = "('created','uploading','uploaded','processing','ready','failed','deleted')"


class MediaAsset(Base):
    """One video file of a movie, episode or trailer. `owner_id` points at a title (movie,
    trailer) or an episode; it is not a foreign key because the target table depends on the type."""

    __tablename__ = "media_assets"
    __table_args__ = (
        CheckConstraint("owner_type IN ('movie','episode','trailer')", name="ck_assets_owner_type"),
        CheckConstraint(f"status IN {_STATUSES}", name="ck_assets_status"),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0", name="ck_assets_duration"
        ),
        CheckConstraint(
            "source_size_bytes IS NULL OR source_size_bytes >= 0", name="ck_assets_size"
        ),
        # Provider ids are unique per provider, so a webhook can find its asset unambiguously.
        UniqueConstraint("provider", "provider_asset_id", name="uq_assets_provider_asset"),
        # At most one live asset per owner and type (a replacement deletes the old one first).
        Index(
            "uq_assets_live_owner",
            "owner_type",
            "owner_id",
            unique=True,
            postgresql_where=text("status <> 'deleted'"),
        ),
        Index("ix_assets_status_updated", "status", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(String(10), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_asset_id: Mapped[str | None] = mapped_column(Text)
    playback_id: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default="created")
    failure_reason: Mapped[str | None] = mapped_column(String(500))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    source_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    checksum: Mapped[str | None] = mapped_column(String(128))
    renditions: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    thumbnails: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UploadSession(Base):
    __tablename__ = "upload_sessions"
    __table_args__ = (
        CheckConstraint(
            "state IN ('open','completed','expired','aborted')", name="ck_upload_state"
        ),
        CheckConstraint("bytes_received >= 0", name="ck_upload_bytes"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploader_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    provider_upload_id: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bytes_received: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    state: Mapped[str] = mapped_column(String(10), nullable=False, server_default="open")
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ProviderEvent(Base):
    """Every provider notification we accepted. The unique key is what makes redelivery harmless."""

    __tablename__ = "provider_events"
    __table_args__ = (UniqueConstraint("provider", "event_id", name="uq_provider_event"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    event_id: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    processed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
