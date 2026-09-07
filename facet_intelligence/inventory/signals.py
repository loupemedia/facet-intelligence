"""Daily inventory signals — diff, emit, snapshot."""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Optional

from config.tenants import get_tenant
from facet_intelligence.events.adapters.webhook_adapter import deliver_tenant_event
from facet_intelligence.events.emitter import (
    emit_diamond_disappeared,
    emit_diamond_price_dropped,
)
from facet_intelligence.inventory.better_match import detect_better_matches
from facet_intelligence.inventory.diff import detect_disappearances, detect_price_drops
from facet_intelligence.inventory.event_store import EmittedEventStore, MissTrackingStore
from facet_intelligence.inventory.snapshot import SnapshotStore

logger = logging.getLogger(__name__)


@dataclass
class SignalRunResult:
    tenant_id: str
    snapshot_date: date
    snapshot_rows: int
    price_drops: int = 0
    disappearances: int = 0
    events_delivered: int = 0
    events_skipped_duplicate: int = 0
    event_ids: list[str] = field(default_factory=list)


def _publish_event(
    tenant_id: str,
    event: dict[str, Any],
    *,
    event_store: EmittedEventStore,
    deliver: bool = True,
) -> bool:
    if not event_store.record_if_new(tenant_id, event):
        return False
    if deliver:
        deliver_tenant_event(tenant_id, event)
    return True


def run_daily_inventory_signals(
    tenant_id: str,
    as_of: date,
    *,
    snapshot_store: Optional[SnapshotStore] = None,
    miss_store: Optional[MissTrackingStore] = None,
    event_store: Optional[EmittedEventStore] = None,
    deliver_webhooks: bool = True,
) -> SignalRunResult:
    """Run price-drop + disappearance detection, emit events, capture snapshot."""
    tenant = get_tenant(tenant_id)
    grace_days = tenant["grace_period_days"]
    min_drop_pct = tenant["price_drop_min_pct"]

    snapshots = snapshot_store or SnapshotStore()
    misses = miss_store or MissTrackingStore()
    events = event_store or EmittedEventStore()

    yesterday = as_of - timedelta(days=1)
    current = snapshots.fetch_live_listings(tenant_id)
    previous = snapshots.fetch_snapshot(tenant_id, yesterday)

    result = SignalRunResult(tenant_id=tenant_id, snapshot_date=as_of, snapshot_rows=0)

    if previous:
        for price_drop in detect_price_drops(
            current=current,
            previous=previous,
            min_drop_pct=min_drop_pct,
        ):
            event = emit_diamond_price_dropped(tenant_id, price_drop, as_of=as_of)
            if _publish_event(tenant_id, event, event_store=events, deliver=deliver_webhooks):
                result.price_drops += 1
                result.events_delivered += 1
                result.event_ids.append(event["event_id"])
            else:
                result.events_skipped_duplicate += 1

        miss_tracking = misses.load(tenant_id)
        disappeared, new_tracking = detect_disappearances(
            current=current,
            previous=previous,
            miss_tracking=miss_tracking,
            as_of=as_of,
            grace_days=grace_days,
        )
        for disappearance in disappeared:
            event = emit_diamond_disappeared(tenant_id, disappearance, as_of=as_of)
            if _publish_event(tenant_id, event, event_store=events, deliver=deliver_webhooks):
                result.disappearances += 1
                result.events_delivered += 1
                result.event_ids.append(event["event_id"])
                new_tracking.pop(disappearance.listing_id, None)
            else:
                result.events_skipped_duplicate += 1
        misses.save(tenant_id, new_tracking)
    else:
        logger.info(
            "No snapshot for %s on %s; skipping diff (first run)",
            tenant_id,
            yesterday.isoformat(),
        )

    detect_better_matches(tenant_id, as_of)

    result.snapshot_rows = snapshots.capture_snapshot(tenant_id, as_of)
    return result
