"""profiles

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("avatar", sa.String(16), nullable=False, server_default="avatar-1"),
        sa.Column("language", sa.String(8), nullable=False, server_default="en"),
        sa.Column("maturity_limit", sa.String(8), nullable=False, server_default="13+"),
        sa.Column("autoplay_next", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("data_saver", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("subtitle_prefs", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint("maturity_limit IN ('all','7+','13+','16+','18+')",
                           name="ck_profiles_maturity"),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])
    op.create_index("uq_profiles_user_name", "profiles", ["user_id", sa.text("lower(name)")],
                    unique=True)
    # Every existing account gets a default adult profile.
    op.execute(
        "INSERT INTO profiles (id, user_id, name, maturity_limit) "
        "SELECT gen_random_uuid(), id, 'Me', '18+' FROM users"
    )


def downgrade() -> None:
    op.drop_table("profiles")
