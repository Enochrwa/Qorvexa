import datetime as dt
import re
import uuid
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

ALLOWED_EXTENSIONS = (".mp4", ".m4v", ".mov", ".mkv", ".webm")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class UploadRequest(BaseModel):
    """What the browser is about to upload. The bytes themselves go straight to the provider."""

    model_config = ConfigDict(extra="forbid")
    filename: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    size_bytes: Annotated[int, Field(gt=0)]

    @field_validator("filename")
    @classmethod
    def _safe_filename(cls, value: str) -> str:
        if _CONTROL.search(value) or "/" in value or "\\" in value:
            raise ValueError("Use a plain file name without paths")
        if not value.lower().endswith(ALLOWED_EXTENSIONS):
            raise ValueError(f"Use one of: {', '.join(ALLOWED_EXTENSIONS)}")
        return value


class UploadTicketOut(BaseModel):
    """Where the browser sends the file. Short-lived; contains no long-term secret."""

    asset_id: uuid.UUID
    provider: str
    url: str
    method: Literal["PUT", "POST"]
    headers: dict[str, str]
    fields: dict[str, str]
    expires_at: dt.datetime
    part_size_bytes: int | None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_type: str
    owner_id: uuid.UUID
    status: str
    failure_reason: str | None
    duration_seconds: int | None
    source_size_bytes: int | None
    renditions: list[dict[str, Any]]
    created_at: dt.datetime
    updated_at: dt.datetime


class WebhookAck(BaseModel):
    result: str
