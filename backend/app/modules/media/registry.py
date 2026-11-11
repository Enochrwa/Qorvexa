"""Chooses the configured provider. The rest of the app asks for `VideoProvider`, never a vendor."""

from functools import lru_cache

from app.core.config import get_settings
from app.modules.media.provider import ProviderError, VideoProvider
from app.modules.media.providers.fake import FakeProvider


class ProviderNotConfigured(ProviderError):
    pass


@lru_cache
def get_video_provider() -> VideoProvider:
    name = get_settings().video_provider
    if name == "fake":
        return FakeProvider()
    # "local" and "cloudinary" arrive with their providers (Sprint 2); until then fail loudly
    # at first use instead of silently falling back to something else.
    raise ProviderNotConfigured(f"VIDEO_PROVIDER={name!r} is not available yet")
