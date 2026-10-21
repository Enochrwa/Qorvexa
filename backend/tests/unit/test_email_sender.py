import smtplib

import pytest

from app.modules.auth.email import SmtpEmailSender


async def test_smtp_failure_does_not_raise_or_leak_body(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def boom(*_a: object, **_k: object) -> None:
        raise ConnectionRefusedError("down")

    monkeypatch.setattr(smtplib, "SMTP", boom)
    await SmtpEmailSender().send("a@example.com", "Subject", "secret-token-body")
    assert "email delivery failed" in caplog.text
    assert "secret-token-body" not in caplog.text


async def test_smtp_success_sends_message(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[str] = []

    class FakeSMTP:
        def __init__(self, *_a: object, **_k: object) -> None: ...
        def __enter__(self) -> "FakeSMTP":
            return self

        def __exit__(self, *_a: object) -> None: ...
        def send_message(self, msg: object) -> None:
            sent.append(str(msg["Subject"]))  # type: ignore[index]

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    await SmtpEmailSender().send("a@example.com", "Hello", "body")
    assert sent == ["Hello"]
