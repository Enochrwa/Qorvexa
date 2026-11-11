import pytest

from app.core.config import get_settings
from app.modules.media.providers.fake import FakeProvider
from app.modules.media.registry import ProviderNotConfigured, get_video_provider


def _fresh(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    monkeypatch.setenv("VIDEO_PROVIDER", name)
    get_settings.cache_clear()
    get_video_provider.cache_clear()


def test_the_fake_provider_is_available_for_development(monkeypatch: pytest.MonkeyPatch) -> None:
    _fresh(monkeypatch, "fake")
    try:
        assert isinstance(get_video_provider(), FakeProvider)
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
        get_video_provider.cache_clear()


@pytest.mark.parametrize("name", ["local", "cloudinary", "typo"])
def test_a_provider_that_does_not_exist_yet_fails_loudly_not_silently(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    _fresh(monkeypatch, name)
    try:
        with pytest.raises(ProviderNotConfigured, match=name):
            get_video_provider()
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
        get_video_provider.cache_clear()
