"""Auth abuse limits. Numbers live here so they are easy to review and tune."""

import hashlib

from app.core.ratelimit import Limiter

MINUTE, HOUR = 60, 3600

REGISTER_PER_IP = (5, HOUR)
VERIFY_PER_IP = (20, HOUR)
LOGIN_PER_IP = (20, 15 * MINUTE)
LOGIN_FAILS_PER_EMAIL_AND_IP = (5, 15 * MINUTE)  # lockout threshold
LOGIN_FAILS_PER_EMAIL = (30, HOUR)  # distributed attack on one account
FORGOT_PER_IP = (5, HOUR)
FORGOT_EMAILS_PER_ADDRESS = (3, HOUR)  # extra requests are silently not sent
RESET_PER_IP = (10, HOUR)
REFRESH_PER_IP = (120, HOUR)


def _id(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()[:32]


async def before_login(limiter: Limiter, ip: str, email: str) -> None:
    """Raise 429 if the IP is too busy or this email+IP pair or email is locked out."""
    await limiter.enforce(f"rl:login:ip:{ip}", *LOGIN_PER_IP)
    await limiter.check(f"rl:login:fail:{_id(email)}:{ip}", LOGIN_FAILS_PER_EMAIL_AND_IP[0])
    await limiter.check(f"rl:login:fail:{_id(email)}", LOGIN_FAILS_PER_EMAIL[0])


async def login_failed(limiter: Limiter, ip: str, email: str) -> None:
    """Count a failure whether or not the account exists, so lockout reveals nothing."""
    await limiter.hit(f"rl:login:fail:{_id(email)}:{ip}", *LOGIN_FAILS_PER_EMAIL_AND_IP)
    await limiter.hit(f"rl:login:fail:{_id(email)}", *LOGIN_FAILS_PER_EMAIL)


async def login_succeeded(limiter: Limiter, ip: str, email: str) -> None:
    await limiter.reset(f"rl:login:fail:{_id(email)}:{ip}")


async def allow_forgot_email(limiter: Limiter, email: str) -> bool:
    allowed, _ = await limiter.hit(f"rl:forgot:email:{_id(email)}", *FORGOT_EMAILS_PER_ADDRESS)
    return allowed
