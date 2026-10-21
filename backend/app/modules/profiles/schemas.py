import re
import uuid
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
Avatar = Annotated[str, StringConstraints(pattern=r"^avatar-([1-9]|1[0-2])$")]
Language = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$")]
Maturity = Literal["all", "7+", "13+", "16+", "18+"]
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _no_control_chars(value: str) -> str:
    if _CONTROL.search(value):
        raise ValueError("Name contains invalid characters")
    return value


class SubtitlePrefs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    language: Language | None = None
    size: Literal["small", "medium", "large"] = "medium"


class ProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Name
    avatar: Avatar = "avatar-1"
    language: Language = "en"
    maturity_limit: Maturity = "13+"
    autoplay_next: bool = True
    data_saver: bool = False
    subtitle_prefs: SubtitlePrefs = Field(default_factory=SubtitlePrefs)

    @model_validator(mode="after")
    def _name_ok(self) -> "ProfileCreate":
        _no_control_chars(self.name)
        return self


class ProfilePatch(BaseModel):
    """Partial update. Unknown fields (e.g. user_id) are rejected; explicit nulls are rejected."""

    model_config = ConfigDict(extra="forbid")
    name: Name | None = None
    avatar: Avatar | None = None
    language: Language | None = None
    maturity_limit: Maturity | None = None
    autoplay_next: bool | None = None
    data_saver: bool | None = None
    subtitle_prefs: SubtitlePrefs | None = None

    @model_validator(mode="after")
    def _validate(self) -> "ProfilePatch":
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        if self.name is not None:
            _no_control_chars(self.name)
        return self

    def changes(self) -> dict[str, Any]:
        data = self.model_dump(exclude_unset=True)
        return data


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    avatar: str
    language: str
    maturity_limit: str
    autoplay_next: bool
    data_saver: bool
    subtitle_prefs: dict[str, Any]
