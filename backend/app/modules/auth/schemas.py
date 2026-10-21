from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.auth.security import COMMON_PASSWORDS

Password = Annotated[str, Field(min_length=10, max_length=128)]


def _check_not_common(value: str) -> str:
    if value.lower() in COMMON_PASSWORDS:
        raise ValueError("Password is too common")
    return value


class RegisterIn(BaseModel):
    email: EmailStr
    password: Password

    _common = field_validator("password")(_check_not_common)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    password: Password

    _common = field_validator("password")(_check_not_common)


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth token type label, not a secret
    expires_in: int


class MeOut(BaseModel):
    id: str
    email: str
    role: str
    email_verified: bool


class AcceptedOut(BaseModel):
    status: str = "accepted"
