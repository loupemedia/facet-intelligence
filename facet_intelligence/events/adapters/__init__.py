"""External webhook delivery (Principle 13)."""

from shared.services.webhook.sender import deliver_webhook

__all__ = ["deliver_webhook"]
