"""Daily inventory signals — diff, emit, snapshot."""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any, Optional

from config.tenants import get_tenant, tenant_webhook_url
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


class PublishResult(str, Enum):
    """Outcome of attempting to deliver and persist one inventory signal event."""

    EMITTED = "emitted"
    DUPLICATE = "duplicate"
    DELIVERY_FAILED = "delivery_failed"
    NO_WEBHOOK_URL = "no_webhook_url"
    DRY_RUN = "dry_run"


@dataclass
class SignalRunResult:
    tenant_id: str
    snapshot_date: date
    snapshot_rows: int
    price_drops: int = 0
    disappearances: int = 0
    events_delivered: int = 0
    events_skipped_duplicate: int = 0
    events_delivery_failed: int = 0
    events_skipped_no_webhook: int = 0
    event_ids: list[str] = field(default_factory=list)


def _publish_event(
    tenant_id: str,
    event: dict[str, Any],
    *,
    event_store: EmittedEventStore,
    deliver: bool = True,
) -> PublishResult:
    """Deliver first, then record dedupe — only after successful webhook POST."""
    event_id = event["event_id"]
    if event_store.is_emitted(tenant_id, event_id):
        return PublishResult.DUPLICATE

    if not deliver:
        return PublishResult.DRY_RUN

    if not tenant_webhook_url(tenant_id):
        logger.warning(
            "No webhook URL for tenant %s; event %s not delivered or deduped",
            tenant_id,
            event_id,
        )
        return PublishResult.NO_WEBHOOK_URL

    try:
        deliver_tenant_event(tenant_id, event)
    except Exception:
        logger.error(
            "Webhook delivery failed for tenant %s event %s; dedupe not recorded",
            tenant_id,
            event_id,
            exc_info=True,
        )
        return PublishResult.DELIVERY_FAILED

    if not event_store.record_if_new(tenant_id, event):
        logger.warning(
            "Webhook delivered for tenant %s event %s but dedupe insert was duplicate",
            tenant_id,
            event_id,
        )
        return PublishResult.DUPLICATE

    return PublishResult.EMITTED


def _apply_price_drop_outcome(
    result: SignalRunResult,
    outcome: PublishResult,
    *,
    event_id: str,
) -> None:
    result.price_drops += 1
    if outcome == PublishResult.EMITTED:
        result.events_delivered += 1
        result.event_ids.append(event_id)
    elif outcome == PublishResult.DUPLICATE:
        result.events_skipped_duplicate += 1
    elif outcome == PublishResult.DELIVERY_FAILED:
        result.events_delivery_failed += 1
    elif outcome == PublishResult.NO_WEBHOOK_URL:
        result.events_skipped_no_webhook += 1


def _apply_disappearance_outcome(
    result: SignalRunResult,
    outcome: PublishResult,
    *,
    event_id: str,
) -> bool:
    """Return True when disappearance miss-tracking may be cleared for this listing."""
    result.disappearances += 1
    if outcome == PublishResult.EMITTED:
        result.events_delivered += 1
        result.event_ids.append(event_id)
        return True
    if outcome == PublishResult.DUPLICATE:
        result.events_skipped_duplicate += 1
        return True
    if outcome == PublishResult.DELIVERY_FAILED:
        result.events_delivery_failed += 1
    elif outcome == PublishResult.NO_WEBHOOK_URL:
        result.events_skipped_no_webhook += 1
    return False


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

    result = SignalRunResult(
        tenant_id=tenant_id,
        snapshot_date=as_of,
        snapshot_rows=0,
    )

    try:
        if previous:
            for price_drop in detect_price_drops(
                current=current,
                previous=previous,
                min_drop_pct=min_drop_pct,
            ):
                event = emit_diamond_price_dropped(tenant_id, price_drop, as_of=as_of)
                outcome = _publish_event(
                    tenant_id,
                    event,
                    event_store=events,
                    deliver=deliver_webhooks,
                )
                _apply_price_drop_outcome(result, outcome, event_id=event["event_id"])

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
                outcome = _publish_event(
                    tenant_id,
                    event,
                    event_store=events,
                    deliver=deliver_webhooks,
                )
                if _apply_disappearance_outcome(result, outcome, event_id=event["event_id"]):
                    new_tracking.pop(disappearance.listing_id, None)
            misses.save(tenant_id, new_tracking)
        else:
            logger.info(
                "No snapshot for %s on %s; skipping diff (first run)",
                tenant_id,
                yesterday.isoformat(),
            )

        detect_better_matches(tenant_id, as_of)
    finally:
        result.snapshot_rows = snapshots.capture_snapshot(tenant_id, as_of)

    return result
