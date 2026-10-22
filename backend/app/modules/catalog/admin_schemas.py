import datetime as dt
import re
import uuid
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")  # allow \t \n \r in long text


def _https_url(value: str) -> str:
    if not value.startswith("https://") or re.search(r"\s", value):
        raise ValueError("Must be an https:// URL without spaces")
    return value


def _clean(value: str) -> str:
    if _CONTROL.search(value):
        raise ValueError("Contains invalid control characters")
    return value


Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=120)]
Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    AfterValidator(_clean),
]
LongText = Annotated[str, StringConstraints(max_length=5000), AfterValidator(_clean)]
Url = Annotated[str, StringConstraints(max_length=2048), AfterValidator(_https_url)]
Language = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$")]
Country = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
Year = Annotated[int, Field(ge=1888, le=2100)]
Rating = Literal["all", "7+", "13+", "16+", "18+"]
TitleType = Literal["movie", "series"]
Role = Literal["actor", "director", "writer"]


class CastIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
        AfterValidator(_clean),
    ]
    role: Role
    billing_order: Annotated[int, Field(ge=0, le=999)] = 0


def _unique_cast(cast: list[CastIn]) -> None:
    keys = [(c.name.lower(), c.role) for c in cast]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate cast entry")


class TitleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: Slug | None = None
    type: TitleType
    name: Name
    original_name: Name | None = None
    synopsis: LongText | None = None
    release_year: Year | None = None
    maturity_rating: Rating = "18+"  # safest default; lower it deliberately
    language: Language | None = None
    country: Country | None = None
    poster_url: Url | None = None
    backdrop_url: Url | None = None
    downloads_enabled: bool = False
    genres: Annotated[list[Slug], Field(max_length=20)] = Field(default_factory=list)
    cast: Annotated[list[CastIn], Field(max_length=50)] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> "TitleCreate":
        if len(set(self.genres)) != len(self.genres):
            raise ValueError("Duplicate genre")
        _unique_cast(self.cast)
        return self


_NULLABLE = {
    "original_name",
    "synopsis",
    "release_year",
    "language",
    "country",
    "poster_url",
    "backdrop_url",
}


class TitlePatch(BaseModel):
    """Partial update. `slug`, `type` and `status` cannot be changed here (extra fields are 422)."""

    model_config = ConfigDict(extra="forbid")
    name: Name | None = None
    original_name: Name | None = None
    synopsis: LongText | None = None
    release_year: Year | None = None
    maturity_rating: Rating | None = None
    language: Language | None = None
    country: Country | None = None
    poster_url: Url | None = None
    backdrop_url: Url | None = None
    downloads_enabled: bool | None = None
    genres: Annotated[list[Slug], Field(max_length=20)] | None = None
    cast: Annotated[list[CastIn], Field(max_length=50)] | None = None

    @model_validator(mode="after")
    def _check(self) -> "TitlePatch":
        for field in self.model_fields_set - _NULLABLE:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        if self.genres is not None and len(set(self.genres)) != len(self.genres):
            raise ValueError("Duplicate genre")
        if self.cast is not None:
            _unique_cast(self.cast)
        return self


class PublishIn(BaseModel):
    """A future `publish_at` embargoes the title (published but hidden until then)."""

    model_config = ConfigDict(extra="forbid")
    publish_at: dt.datetime | None = None
    available_until: dt.datetime | None = None

    @model_validator(mode="after")
    def _check(self) -> "PublishIn":
        for field in ("publish_at", "available_until"):
            value = getattr(self, field)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{field} must include a timezone")
        return self


class SeasonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    number: Annotated[int, Field(ge=0, le=100)]
    name: Name | None = None
    synopsis: LongText | None = None


class SeasonPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    number: Annotated[int, Field(ge=0, le=100)] | None = None
    name: Name | None = None
    synopsis: LongText | None = None

    @model_validator(mode="after")
    def _check(self) -> "SeasonPatch":
        if "number" in self.model_fields_set and self.number is None:
            raise ValueError("number cannot be null")
        return self


Seconds = Annotated[int, Field(ge=0, le=43200)]


class EpisodeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    number: Annotated[int, Field(ge=1, le=500)]
    name: Name
    synopsis: LongText | None = None
    runtime_seconds: Annotated[int, Field(ge=1, le=43200)] | None = None
    air_date: dt.date | None = None
    intro_start: Seconds | None = None
    intro_end: Seconds | None = None
    recap_end: Seconds | None = None
    status: Literal["draft", "published"] = "draft"


class EpisodePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    number: Annotated[int, Field(ge=1, le=500)] | None = None
    name: Name | None = None
    synopsis: LongText | None = None
    runtime_seconds: Annotated[int, Field(ge=1, le=43200)] | None = None
    air_date: dt.date | None = None
    intro_start: Seconds | None = None
    intro_end: Seconds | None = None
    recap_end: Seconds | None = None
    status: Literal["draft", "published"] | None = None

    @model_validator(mode="after")
    def _check(self) -> "EpisodePatch":
        for field in ("number", "name", "status"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class ReorderIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    episode_ids: Annotated[list[uuid.UUID], Field(min_length=1, max_length=500)]


# ---- output ----------------------------------------------------------------------------------


class AdminTitleItem(BaseModel):
    id: uuid.UUID
    slug: str
    type: str
    name: str
    status: str
    state: Literal["draft", "archived", "scheduled", "live", "expired"]
    maturity_rating: str
    release_year: int | None
    publish_at: dt.datetime | None
    available_until: dt.datetime | None
    updated_at: dt.datetime


class AdminTitleList(BaseModel):
    items: list[AdminTitleItem]
    total: int


class CastOut(BaseModel):
    name: str
    role: str
    billing_order: int


class AdminTitle(AdminTitleItem):
    original_name: str | None
    synopsis: str | None
    language: str | None
    country: str | None
    poster_url: str | None
    backdrop_url: str | None
    downloads_enabled: bool
    created_at: dt.datetime
    genres: list[str]
    cast: list[CastOut]


class AdminEpisode(BaseModel):
    id: uuid.UUID
    number: int
    name: str
    synopsis: str | None
    runtime_seconds: int | None
    air_date: dt.date | None
    intro_start: int | None
    intro_end: int | None
    recap_end: int | None
    status: str


class AdminSeason(BaseModel):
    id: uuid.UUID
    title_id: uuid.UUID
    number: int
    name: str | None
    synopsis: str | None
    episodes: list[AdminEpisode] = Field(default_factory=list)


def changed_fields(model: BaseModel) -> list[str]:
    return sorted(model.model_fields_set)


__all__: list[Any] = ["AdminTitle", "TitleCreate", "TitlePatch"]
