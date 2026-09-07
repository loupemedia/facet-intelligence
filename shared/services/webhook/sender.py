"""HTTP webhook delivery adapter."""

import logging

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 15.0


def deliver_webhook(url: str, payload: dict, *, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
    """POST a canonical event payload to a tenant webhook URL."""
    response = httpx.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    logger.info("Webhook POST %s returned %s", url, response.status_code)
