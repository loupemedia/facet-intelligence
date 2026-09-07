"""Deliver canonical events to a tenant webhook URL."""

import logging
from typing import Any

from config.tenants import tenant_webhook_url
from shared.services.webhook.sender import deliver_webhook

logger = logging.getLogger(__name__)


def deliver_tenant_event(tenant_id: str, event: dict[str, Any]) -> bool:
    """POST event to tenant webhook when configured. Returns True if delivered."""
    url = tenant_webhook_url(tenant_id)
    if not url:
        logger.info(
            "No webhook URL for tenant %s; event %s logged only",
            tenant_id,
            event.get("event_id"),
        )
        return False
    deliver_webhook(url, event)
    logger.info(
        "Delivered %s to webhook for tenant %s",
        event.get("event_type"),
        tenant_id,
    )
    return True
