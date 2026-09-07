"""Canonical inventory event emission."""

import hashlib
import logging
from datetime import date, datetime
from typing import Any

from facet_intelligence.inventory.models import Disappearance, PriceDrop

logger = logging.getLogger(__name__)

__all__ = [
    "build_event_id",
    "build_listing_event_id",
    "emit_diamond_disappeared",
    "emit_diamond_price_dropped",
    "emit_inventory_synced",
]


def build_event_id(tenant_id: str, event_type: str, event_date: date) -> str:
    """Idempotent tenant-level event_id."""
    raw = f"{tenant_id}:{event_type}:{event_date.isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def build_listing_event_id(
    tenant_id: str,
    listing_id: str,
    trigger: str,
    event_date: date,
) -> str:
    """Idempotent listing-level event_id: hash(tenant, listing_id, trigger, date)."""
    raw = f"{tenant_id}:{listing_id}:{trigger}:{event_date.isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def emit_inventory_synced(
    tenant_id: str,
    *,
    listing_count: int,
    rows_upserted: int,
    synced_at: datetime,
) -> dict[str, Any]:
    """Build inventory.synced event."""
    event_date = synced_at.date()
    event_id = build_event_id(tenant_id, "inventory.synced", event_date)
    event = {
        "event_type": "inventory.synced",
        "event_id": event_id,
        "tenant_id": tenant_id,
        "payload": {
            "listing_count": listing_count,
            "rows_upserted": rows_upserted,
            "synced_at": synced_at.isoformat(),
        },
    }
    logger.info(
        "Built inventory.synced for tenant %s (event_id=%s, listings=%d)",
        tenant_id,
        event_id,
        listing_count,
    )
    return event


def emit_diamond_disappeared(
    tenant_id: str,
    disappearance: Disappearance,
    *,
    as_of: date,
    alternatives: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build diamond.disappeared event."""
    event_id = build_listing_event_id(
        tenant_id,
        disappearance.listing_id,
        "diamond.disappeared",
        as_of,
    )
    event = {
        "event_type": "diamond.disappeared",
        "event_id": event_id,
        "tenant_id": tenant_id,
        "payload": {
            "listing_id": disappearance.listing_id,
            "stone_key": disappearance.stone_key,
            "retailer_code": disappearance.retailer_code,
            "cert_lab": disappearance.cert_lab,
            "cert_number": disappearance.cert_number,
            "last_price": disappearance.last_price,
            "currency": disappearance.currency,
            "product_url": disappearance.product_url,
            "first_missing_date": disappearance.first_missing_date.isoformat(),
            "alternatives": alternatives or [],
        },
    }
    logger.info(
        "Built diamond.disappeared for %s listing %s",
        tenant_id,
        disappearance.listing_id,
    )
    return event


def emit_diamond_price_dropped(
    tenant_id: str,
    price_drop: PriceDrop,
    *,
    as_of: date,
    alternatives: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build diamond.price_dropped event."""
    event_id = build_listing_event_id(
        tenant_id,
        price_drop.listing_id,
        "diamond.price_dropped",
        as_of,
    )
    event = {
        "event_type": "diamond.price_dropped",
        "event_id": event_id,
        "tenant_id": tenant_id,
        "payload": {
            "listing_id": price_drop.listing_id,
            "stone_key": price_drop.stone_key,
            "retailer_code": price_drop.retailer_code,
            "cert_lab": price_drop.cert_lab,
            "cert_number": price_drop.cert_number,
            "old_price": price_drop.old_price,
            "new_price": price_drop.new_price,
            "drop_pct": price_drop.drop_pct,
            "currency": price_drop.currency,
            "product_url": price_drop.product_url,
            "alternatives": alternatives or [],
        },
    }
    logger.info(
        "Built diamond.price_dropped for %s listing %s (%.1f%%)",
        tenant_id,
        price_drop.listing_id,
        price_drop.drop_pct,
    )
    return event
