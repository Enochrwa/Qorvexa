"""Serve the built single-page app from the API, so both share one origin (ADR-0015).

Why: the refresh cookie is SameSite=Lax, and browsers refuse to store it when the app and the
API are on different sites. Serving both from one service keeps them on one site at no cost.
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import Response
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

log = logging.getLogger(__name__)

# Hashed build assets never change, so they can be cached forever; the HTML entry point cannot.
_IMMUTABLE = "public, max-age=31536000, immutable"
_NO_CACHE = "no-cache"

# The app only talks to its own origin. Images and media may come from any https host (the
# media provider), and styles allow inline because components set colours through `style`.
_CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' https: data:",
        "media-src 'self' https: blob:",
        "connect-src 'self' https:",
        "font-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)
_HTML_HEADERS = {
    "Content-Security-Policy": _CSP,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cache-Control": _NO_CACHE,
}


class SpaFiles(StaticFiles):
    """Static files with a fallback to index.html for client-side routes.

    Unknown paths with a file extension and anything under /api stay real 404s, so a typo in an
    asset or endpoint is never answered with the app's HTML.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            response = await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or not self._is_client_route(path):
                raise
            response = await super().get_response("index.html", scope)
        if response.status_code == 200:
            self._set_headers(response, path)
        return response

    @staticmethod
    def _is_client_route(path: str) -> bool:
        if path.startswith(("api/", "assets/")) or path == "api":
            return False
        return "." not in Path(path).name

    @staticmethod
    def _set_headers(response: Response, path: str) -> None:
        if path.startswith("assets/"):
            response.headers["Cache-Control"] = _IMMUTABLE
            response.headers["X-Content-Type-Options"] = "nosniff"
        elif response.headers.get("content-type", "").startswith("text/html"):
            response.headers.update(_HTML_HEADERS)


def mount_frontend(app: FastAPI, dist_dir: str) -> None:
    """Mount last, so every API route wins. Fails fast if the build is missing."""
    root = Path(dist_dir)
    if not (root / "index.html").is_file():
        raise RuntimeError(
            f"FRONTEND_DIST_DIR={dist_dir!r} has no index.html; build the frontend first"
        )
    app.mount("/", SpaFiles(directory=root, html=True), name="frontend")
    log.info("serving the frontend from %s", root)
