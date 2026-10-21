from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.core.errors import Forbidden, Unauthorized
from app.core.ratelimit import Limiter, client_ip, get_rate_limiter
from app.modules.auth import service, throttle
from app.modules.auth.deps import CurrentUser, require_role
from app.modules.auth.email import EmailSender, get_email_sender
from app.modules.auth.schemas import (
    AcceptedOut,
    AccessTokenOut,
    ForgotIn,
    LoginIn,
    MeOut,
    RegisterIn,
    ResetIn,
    TokenIn,
)

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE = "refresh_token"
COOKIE_PATH = "/api/v1/auth"
CSRF_HEADER_VALUE = "web"

Session = Annotated[AsyncSession, Depends(get_session)]
Sender = Annotated[EmailSender, Depends(get_email_sender)]
RateLimiter = Annotated[Limiter, Depends(get_rate_limiter)]


def _set_cookie(response: Response, raw: str) -> None:
    settings = get_settings()
    response.set_cookie(
        COOKIE,
        raw,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_refresh_ttl_days * 86400,
        path=COOKIE_PATH,
    )


def _require_csrf_header(value: str | None) -> None:
    """Cookie-authenticated endpoints also need a custom header a cross-site form cannot send."""
    if value != CSRF_HEADER_VALUE:
        raise Forbidden("Missing or invalid X-Qorvexa-Client header")


def _token_out(access: str) -> AccessTokenOut:
    return AccessTokenOut(
        access_token=access, expires_in=get_settings().jwt_access_ttl_minutes * 60
    )


@router.post("/register", status_code=202)
async def register(
    request: Request, body: RegisterIn, session: Session, sender: Sender, limiter: RateLimiter
) -> AcceptedOut:
    """Create an account. Always 202, whether or not the email was already registered."""
    await limiter.enforce(f"rl:register:ip:{client_ip(request)}", *throttle.REGISTER_PER_IP)
    await service.register(session, sender, str(body.email), body.password)
    return AcceptedOut()


@router.post("/verify-email", status_code=204)
async def verify_email(
    request: Request, body: TokenIn, session: Session, limiter: RateLimiter
) -> None:
    await limiter.enforce(f"rl:verify:ip:{client_ip(request)}", *throttle.VERIFY_PER_IP)
    await service.verify_email(session, body.token)


@router.post("/login")
async def login(
    request: Request, body: LoginIn, response: Response, session: Session, limiter: RateLimiter
) -> AccessTokenOut:
    ip, email = client_ip(request), str(body.email)
    await throttle.before_login(limiter, ip, email)
    try:
        access, refresh = await service.login(session, email, body.password)
    except Unauthorized:
        await throttle.login_failed(limiter, ip, email)
        raise
    await throttle.login_succeeded(limiter, ip, email)
    _set_cookie(response, refresh)
    return _token_out(access)


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    session: Session,
    limiter: RateLimiter,
    refresh_token: Annotated[str | None, Cookie(alias=COOKIE)] = None,
    x_qorvexa_client: Annotated[str | None, Header()] = None,
) -> AccessTokenOut:
    _require_csrf_header(x_qorvexa_client)
    await limiter.enforce(f"rl:refresh:ip:{client_ip(request)}", *throttle.REFRESH_PER_IP)
    if not refresh_token:
        raise Unauthorized("Invalid session")
    access, new_refresh = await service.refresh(session, refresh_token)
    _set_cookie(response, new_refresh)
    return _token_out(access)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    session: Session,
    user: Annotated[CurrentUser, Depends(require_role("viewer"))],
    refresh_token: Annotated[str | None, Cookie(alias=COOKIE)] = None,
    x_qorvexa_client: Annotated[str | None, Header()] = None,
) -> None:
    _require_csrf_header(x_qorvexa_client)
    await service.logout(session, user.id, refresh_token)
    response.delete_cookie(COOKIE, path=COOKIE_PATH)


@router.post("/password/forgot", status_code=202)
async def forgot_password(
    request: Request, body: ForgotIn, session: Session, sender: Sender, limiter: RateLimiter
) -> AcceptedOut:
    await limiter.enforce(f"rl:forgot:ip:{client_ip(request)}", *throttle.FORGOT_PER_IP)
    email = str(body.email)
    if await throttle.allow_forgot_email(limiter, email):  # over the cap: still 202, no mail
        await service.forgot_password(session, sender, email)
    return AcceptedOut()


@router.post("/password/reset", status_code=204)
async def reset_password(
    request: Request, body: ResetIn, session: Session, limiter: RateLimiter
) -> None:
    await limiter.enforce(f"rl:reset:ip:{client_ip(request)}", *throttle.RESET_PER_IP)
    await service.reset_password(session, body.token, body.password)


@router.get("/me")
async def me(user: Annotated[CurrentUser, Depends(require_role("viewer"))]) -> MeOut:
    return MeOut(
        id=str(user.id), email=user.email, role=user.role, email_verified=user.email_verified
    )
