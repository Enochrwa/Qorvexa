# Media providers

The app talks to video vendors only through `VideoProvider` (`backend/app/modules/media/provider.py`, ADR-0003). Each vendor (Local MinIO+FFmpeg, Cloudinary, later Mux or R2) is one class that knows how to authorise an upload, verify a webhook and make a playback URL. Nothing else in the app knows a vendor's name, so a provider can be replaced without rewriting the application.

Video bytes never pass through the API: `create_upload` returns where the **browser** sends the file (URL, method, headers or form fields, expiry, part size).

## The methods

| Method | Must do |
|---|---|
| `create_upload(asset_id, filename, size)` | Return an `UploadTicket`: HTTPS URL, method, a **future** expiry, a provider upload id unique per asset. No long-lived secrets in the ticket. |
| `handle_webhook(headers, body)` | **Verify first**, then parse into an `AssetEvent`. Raise `InvalidWebhook` (and only that) for a missing or wrong signature, a tampered body, or a malformed body, even if correctly signed. Header names are case-insensitive. |
| `get_playback(asset, viewer)` | Raise `NotPlayable` unless the asset is `ready` and has a playback id. Return an HTTPS HLS URL built from the playback id (never our internal asset id), with an expiry if the vendor signs URLs. Authorisation (maturity, availability) is decided by the caller before this is called. |
| `get_download(asset, quality)` | `None` if there is no download in that quality, otherwise an HTTPS URL that expires. |
| `delete(asset)` | Remove the media; safe to call twice. |

## Adding a provider

1. Implement the class (and its settings, read from environment variables; never commit credentials).
2. Add `tests/contract/test_<name>_provider_contract.py`: subclass `ProviderContract`, provide a `provider` fixture (configured, **no real network calls**: stub the vendor's HTTP) and a `webhook` fixture that plays the vendor and signs a body exactly as the vendor does. See `test_fake_provider_contract.py`.
3. The contract suite must pass unchanged. If a rule in it does not fit a real vendor, change the contract for **all** providers in one PR with an ADR, not for one.
4. Map the vendor's statuses onto `Status` in the webhook parser. Vendors that only report "ready" are fine: the state machine allows skipping steps.

## The fake provider

`providers/fake.py` is an in-memory provider for tests and local work. It signs webhooks with an HMAC so the contract tests can exercise verification. It is not a vendor and offers no downloads.
