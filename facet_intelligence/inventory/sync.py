"""Inventory sync orchestration — load, persist, emit inventory.synced."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional

from facet_intelligence.events.emitter import emit_inventory_synced
from facet_intelligence.ingestion.db_adapter import load_tenant_listings
from facet_intelligence.inventory.store import ListingStore, SyncStats
from shared.pipeline_date import PIPELINE_TZ

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InventorySyncResult:
    tenant_id: str
    listing_count: int
    rows_upserted: int
    event_id: str
    synced_at: datetime


def sync_tenant_inventory(
    tenant_id: str,
    body: Mapping[str, Any],
    *,
    store: Optional[ListingStore] = None,
) -> InventorySyncResult:
    """Load listings for a tenant, upsert to DB, emit inventory.synced stub."""
    source = str(body.get("source") or "json").lower()
    raw_rows = body.get("listings")
    if raw_rows is None:
        raise ValueError("Request body must include a 'listings' array")

    map_export = source in {"csv", "export", "feed", "db"}
    listings = load_tenant_listings(
        tenant_id,
        source=source,
        rows=list(raw_rows),
        map_export=map_export,
    )

    listing_store = store or ListingStore()
    stats: SyncStats = listing_store.upsert_listings(tenant_id, listings)
    synced_at = datetime.now(PIPELINE_TZ)
    event = emit_inventory_synced(
        tenant_id,
        listing_count=stats.listing_count,
        rows_upserted=stats.rows_upserted,
        synced_at=synced_at,
    )

    logger.info(
        "Inventory sync complete for %s: %d listing(s), event_id=%s",
        tenant_id,
        stats.listing_count,
        event["event_id"],
    )

    return InventorySyncResult(
        tenant_id=tenant_id,
        listing_count=stats.listing_count,
        rows_upserted=stats.rows_upserted,
        event_id=event["event_id"],
        synced_at=synced_at,
    )
