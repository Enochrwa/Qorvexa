"""catalog: titles, seasons, episodes, genres, people

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

RATINGS = "('all','7+','13+','16+','18+')"


def _pk() -> sa.Column:
    return sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True)


def _fk(name: str, target: str) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=True),
                     sa.ForeignKey(target, ondelete="CASCADE"), nullable=False)


def upgrade() -> None:
    now = sa.text("now()")
    op.create_table(
        "titles",
        _pk(),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("type", sa.String(8), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("original_name", sa.String(200)),
        sa.Column("synopsis", sa.Text()),
        sa.Column("release_year", sa.SmallInteger()),
        sa.Column("maturity_rating", sa.String(8), nullable=False, server_default="18+"),
        sa.Column("language", sa.String(8)),
        sa.Column("country", sa.String(2)),
        sa.Column("poster_url", sa.Text()),
        sa.Column("backdrop_url", sa.Text()),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.Column("publish_at", sa.DateTime(timezone=True)),
        sa.Column("available_until", sa.DateTime(timezone=True)),
        sa.Column("downloads_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.CheckConstraint("type IN ('movie','series')", name="ck_titles_type"),
        sa.CheckConstraint("status IN ('draft','scheduled','published','archived')",
                           name="ck_titles_status"),
        sa.CheckConstraint(f"maturity_rating IN {RATINGS}", name="ck_titles_maturity"),
        sa.CheckConstraint("release_year BETWEEN 1888 AND 2100", name="ck_titles_year"),
    )
    op.create_index("ix_titles_status_publish_at", "titles", ["status", "publish_at"])
    op.create_index("ix_titles_created_at_id", "titles", ["created_at", "id"])
    op.create_table(
        "seasons",
        _pk(),
        _fk("title_id", "titles.id"),
        sa.Column("number", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.String(200)),
        sa.Column("synopsis", sa.Text()),
        sa.UniqueConstraint("title_id", "number", name="uq_seasons_title_number"),
        sa.CheckConstraint("number >= 0", name="ck_seasons_number"),
    )
    op.create_table(
        "episodes",
        _pk(),
        _fk("season_id", "seasons.id"),
        sa.Column("number", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("synopsis", sa.Text()),
        sa.Column("runtime_seconds", sa.Integer()),
        sa.Column("air_date", sa.Date()),
        sa.Column("intro_start", sa.Integer()),
        sa.Column("intro_end", sa.Integer()),
        sa.Column("recap_end", sa.Integer()),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.UniqueConstraint("season_id", "number", name="uq_episodes_season_number"),
        sa.CheckConstraint("status IN ('draft','published')", name="ck_episodes_status"),
        sa.CheckConstraint("number >= 1", name="ck_episodes_number"),
        sa.CheckConstraint("runtime_seconds IS NULL OR runtime_seconds > 0",
                           name="ck_episodes_runtime"),
        sa.CheckConstraint(
            "intro_start IS NULL OR intro_end IS NULL OR "
            "(intro_start >= 0 AND intro_end >= intro_start)", name="ck_episodes_intro"),
    )
    op.create_table(
        "genres",
        _pk(),
        sa.Column("name", sa.String(60), nullable=False, unique=True),
        sa.Column("slug", sa.String(60), nullable=False, unique=True),
    )
    op.create_table(
        "title_genres",
        sa.Column("title_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("genre_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_title_genres_genre_title", "title_genres", ["genre_id", "title_id"])
    op.create_table(
        "people",
        _pk(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
    )
    op.create_table(
        "title_people",
        sa.Column("title_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("people.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.String(10), primary_key=True),
        sa.Column("billing_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint("role IN ('actor','director','writer')", name="ck_title_people_role"),
    )


def downgrade() -> None:
    for t in ("title_people", "people", "title_genres", "genres", "episodes", "seasons", "titles"):
        op.drop_table(t)
