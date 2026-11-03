import uuid
from collections.abc import Mapping

import pytest

from app.modules.media.provider import VideoProvider
from app.modules.media.providers.fake import SIGNATURE_HEADER, FakeProvider
from app.modules.media.states import Status
from tests.contract.provider_contract import ProviderContract, Webhook, event_body


@pytest.fixture
def fake() -> FakeProvider:
    return FakeProvider(webhook_secret="contract-test-secret")


@pytest.fixture
def provider(fake: FakeProvider) -> VideoProvider:
    return fake


@pytest.fixture
def webhook(fake: FakeProvider) -> Webhook:
    def make(
        *,
        event_id: str,
        status: Status | None = None,
        asset_id: uuid.UUID | None = None,
        provider_asset_id: str | None = None,
        raw_body: bytes | None = None,
    ) -> tuple[Mapping[str, str], bytes]:
        body = (
            raw_body
            if raw_body is not None
            else event_body(
                event_id=event_id,
                type="asset.updated",
                status=status.value if status else None,
                asset_id=str(asset_id) if asset_id else None,
                provider_asset_id=provider_asset_id,
            )
        )
        return {SIGNATURE_HEADER: fake.sign(body)}, body

    return make


class TestFakeProvider(ProviderContract):
    pass
