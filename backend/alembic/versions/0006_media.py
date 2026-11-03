"""media_assets, upload_sessions, provider_events

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

STATUSES = "('created','uploading','uploaded','processing','ready','failed','deleted')"


def upgrade() -> None:
    now = sa.text("now()")
    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_type", sa.String(10), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("provider_asset_id", sa.Text()),
        sa.Column("playback_id", sa.Text()),
        sa.Column("status", sa.String(12), nullable=False, server_default="created"),
        sa.Column("failure_reason", sa.String(500)),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("source_size_bytes", sa.BigInteger()),
        sa.Column("checksum", sa.String(128)),
        sa.Column("renditions", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("thumbnails", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.CheckConstraint("owner_type IN ('movie','episode','trailer')", name="ck_assets_owner_type"),
        sa.CheckConstraint(f"status IN {STATUSES}", name="ck_assets_status"),
        sa.CheckConstraint("duration_seconds IS NULL OR duration_seconds >= 0", name="ck_assets_duration"),
        sa.CheckConstraint("source_size_bytes IS NULL OR source_size_bytes >= 0", name="ck_assets_size"),
        sa.UniqueConstraint("provider", "provider_asset_id", name="uq_assets_provider_asset"),
    )
    op.create_index("uq_assets_live_owner", "media_assets", ["owner_type", "owner_id"], unique=True,
                    postgresql_where=sa.text("status <> 'deleted'"))
    op.create_index("ix_assets_status_updated", "media_assets", ["status", "updated_at"])
    op.create_table(
        "upload_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("media_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("provider_upload_id", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bytes_received", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("state", sa.String(10), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.CheckConstraint("state IN ('open','completed','expired','aborted')", name="ck_upload_state"),
        sa.CheckConstraint("bytes_received >= 0", name="ck_upload_bytes"),
    )
    op.create_index("ix_upload_sessions_asset_id", "upload_sessions", ["asset_id"])
    op.create_table(
        "provider_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("event_id", sa.String(200), nullable=False),
        sa.Column("type", sa.String(80), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.UniqueConstraint("provider", "event_id", name="uq_provider_event"),
    )


def downgrade() -> None:
    op.drop_table("provider_events")
    op.drop_table("upload_sessions")
    op.drop_table("media_assets")
