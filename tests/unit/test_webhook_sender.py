"""Webhook delivery signing (PRD-FI-001 Epic 2.5 / PRD-009 Epic 5.3).

Test intent: deliver_webhook signs the exact JSON bytes it posts when
FACET_INTELLIGENCE_WEBHOOK_SECRET is set.

Would fail if: httpx.post used json= instead of the signed raw body.
"""

from shared.services.webhook.sender import (
    SIGNATURE_HEADER,
    deliver_webhook,
    encode_webhook_payload,
    sign_webhook_body,
)


def test_encode_webhook_payload_is_stable() -> None:
    payload = {"event_type": "inventory.synced", "event_id": "abc", "tenant_id": "ringspo-us"}
    first = encode_webhook_payload(payload)
    second = encode_webhook_payload(payload)
    assert first == second


def test_deliver_webhook_posts_signed_body(monkeypatch) -> None:
    captured: dict = {}

    class FakeResponse:
        status_code = 202

        @staticmethod
        def raise_for_status() -> None:
            return None

    def fake_post(url, *, content, headers, timeout):
        captured["url"] = url
        captured["content"] = content
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("shared.services.webhook.sender.httpx.post", fake_post)

    payload = {
        "event_type": "diamond.price_dropped",
        "event_id": "evt-1",
        "tenant_id": "ringspo-us",
        "payload": {"stone_key": "GIA:1"},
    }
    secret = "shared-secret"
    deliver_webhook("https://example.test/webhook", payload, webhook_secret=secret)

    raw_body = captured["content"]
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["headers"][SIGNATURE_HEADER] == sign_webhook_body(secret, raw_body)
    assert raw_body == encode_webhook_payload(payload)
