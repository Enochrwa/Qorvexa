import datetime as dt
import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

_RATINGS = "('all','7+','13+','16+','18+')"


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Title(Base):
    __tablename__ = "titles"
    __table_args__ = (
        CheckConstraint("type IN ('movie','series')", name="ck_titles_type"),
        CheckConstraint(
            "status IN ('draft','scheduled','published','archived')", name="ck_titles_status"
        ),
        CheckConstraint(f"maturity_rating IN {_RATINGS}", name="ck_titles_maturity"),
        CheckConstraint("release_year BETWEEN 1888 AND 2100", name="ck_titles_year"),
        Index("ix_titles_status_publish_at", "status", "publish_at"),
        Index("ix_titles_created_at_id", "created_at", "id"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(200))
    synopsis: Mapped[str | None] = mapped_column(Text)
    release_year: Mapped[int | None] = mapped_column(SmallInteger)
    maturity_rating: Mapped[str] = mapped_column(String(8), nullable=False, server_default="18+")
    language: Mapped[str | None] = mapped_column(String(8))
    country: Mapped[str | None] = mapped_column(String(2))
    poster_url: Mapped[str | None] = mapped_column(Text)
    backdrop_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default="draft")
    publish_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    available_until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    downloads_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (
        UniqueConstraint("title_id", "number", name="uq_seasons_title_number"),
        CheckConstraint("number >= 0", name="ck_seasons_number"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    title_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("titles.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    name: Mapped[str | None] = mapped_column(String(200))
    synopsis: Mapped[str | None] = mapped_column(Text)


class Episode(Base):
    __tablename__ = "episodes"
    __table_args__ = (
        UniqueConstraint("season_id", "number", name="uq_episodes_season_number"),
        CheckConstraint("status IN ('draft','published')", name="ck_episodes_status"),
        CheckConstraint("number >= 1", name="ck_episodes_number"),
        CheckConstraint(
            "runtime_seconds IS NULL OR runtime_seconds > 0", name="ck_episodes_runtime"
        ),
        CheckConstraint(
            "intro_start IS NULL OR intro_end IS NULL OR "
            "(intro_start >= 0 AND intro_end >= intro_start)",
            name="ck_episodes_intro",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    synopsis: Mapped[str | None] = mapped_column(Text)
    runtime_seconds: Mapped[int | None] = mapped_column(Integer)
    air_date: Mapped[dt.date | None] = mapped_column(Date)
    intro_start: Mapped[int | None] = mapped_column(Integer)
    intro_end: Mapped[int | None] = mapped_column(Integer)
    recap_end: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(12), nullable=False, server_default="draft")


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)


class TitleGenre(Base):
    __tablename__ = "title_genres"
    __table_args__ = (Index("ix_title_genres_genre_title", "genre_id", "title_id"),)

    title_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True
    )


class Person(Base):
    __tablename__ = "people"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)


class TitlePerson(Base):
    __tablename__ = "title_people"
    __table_args__ = (
        CheckConstraint("role IN ('actor','director','writer')", name="ck_title_people_role"),
    )

    title_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("people.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(10), primary_key=True)
    billing_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")


__all__: list[Any] = [
    "Episode",
    "Genre",
    "Person",
    "Season",
    "Title",
    "TitleGenre",
    "TitlePerson",
]
