import datetime as dt
import uuid

from pydantic import BaseModel


class GenreOut(BaseModel):
    name: str
    slug: str


class TitleListItem(BaseModel):
    id: uuid.UUID
    slug: str
    type: str
    name: str
    release_year: int | None
    maturity_rating: str
    language: str | None
    poster_url: str | None
    genres: list[GenreOut]


class TitleList(BaseModel):
    items: list[TitleListItem]
    next_cursor: str | None


class PersonCredit(BaseModel):
    name: str
    slug: str
    role: str


class TitleDetail(TitleListItem):
    original_name: str | None
    synopsis: str | None
    country: str | None
    backdrop_url: str | None
    downloads_enabled: bool
    cast: list[PersonCredit]
    season_count: int


class EpisodeOut(BaseModel):
    id: uuid.UUID
    number: int
    name: str
    synopsis: str | None
    runtime_seconds: int | None
    air_date: dt.date | None


class SeasonOut(BaseModel):
    number: int
    name: str | None
    synopsis: str | None
    episodes: list[EpisodeOut]
