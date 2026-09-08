"""HTTP webhook delivery adapter."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 15.0
SIGNATURE_HEADER = "X-Facet-Intelligence-Signature"
SIGNATURE_PREFIX = "sha256="


def sign_webhook_body(secret: str, raw_body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return f"{SIGNATURE_PREFIX}{digest}"


def encode_webhook_payload(payload: dict) -> bytes:
    """Canonical JSON bytes used for signing and delivery."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def deliver_webhook(
    url: str,
    payload: dict,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    webhook_secret: str | None = None,
) -> None:
    """POST a canonical event payload to a tenant webhook URL."""
    raw_body = encode_webhook_payload(payload)
    headers = {"Content-Type": "application/json"}
    secret = webhook_secret or os.environ.get("FACET_INTELLIGENCE_WEBHOOK_SECRET")
    if secret:
        headers[SIGNATURE_HEADER] = sign_webhook_body(secret, raw_body)

    response = httpx.post(url, content=raw_body, headers=headers, timeout=timeout)
    response.raise_for_status()
    logger.info("Webhook POST %s returned %s", url, response.status_code)
