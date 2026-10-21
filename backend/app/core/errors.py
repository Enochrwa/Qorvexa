"""Domain exceptions and RFC 9457 problem+json handlers."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"


class DomainError(Exception):
    status = 400
    title = "Bad request"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.title)
        self.detail = detail or self.title


class NotFound(DomainError):
    status = 404
    title = "Not found"


class Unauthorized(DomainError):
    status = 401
    title = "Unauthorized"


class TooManyRequests(DomainError):
    status = 429
    title = "Too many requests"

    def __init__(self, retry_after: int, detail: str | None = None) -> None:
        super().__init__(detail or "Too many requests. Try again later.")
        self.retry_after = max(1, retry_after)


class Conflict(DomainError):
    status = 409
    title = "Conflict"


class Forbidden(DomainError):
    status = 403
    title = "Forbidden"


def _problem(
    request: Request, status: int, title: str, detail: str, **extra: object
) -> JSONResponse:
    body = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "request_id": getattr(request.state, "request_id", None),
        **extra,
    }
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError) -> JSONResponse:
        resp = _problem(request, exc.status, exc.title, exc.detail)
        if exc.status == 401:
            resp.headers["WWW-Authenticate"] = "Bearer"
        if isinstance(exc, TooManyRequests):
            resp.headers["Retry-After"] = str(exc.retry_after)
        return resp

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(request, exc.status_code, "HTTP error", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": [str(p) for p in e["loc"]], "msg": e["msg"], "type": e["type"]}
            for e in exc.errors()
        ]
        return _problem(request, 422, "Validation error", "Invalid request", errors=errors)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        return _problem(request, 500, "Internal server error", "Unexpected error")
