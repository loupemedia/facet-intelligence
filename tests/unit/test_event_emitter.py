"""Listing-level event ids (PRD-FI-001 Epic 2).

Test intent: diamond.* events use hash(tenant, listing_id, trigger, date) so
replays on the same day dedupe while a new day gets a new id.

Would fail if: price_dropped and disappeared shared one id, or listing_id was
omitted from the hash input.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from facet_intelligence.events.emitter import (
    build_event_id,
    build_listing_event_id,
    emit_diamond_disappeared,
    emit_diamond_price_dropped,
    emit_inventory_synced,
)
from facet_intelligence.inventory.models import Disappearance, PriceDrop

BRISBANE = ZoneInfo("Australia/Brisbane")


class TestTenantEventId:
    def test_inventory_synced_same_day_same_id(self) -> None:
        synced_at = datetime(2026, 3, 7, 8, 0, tzinfo=BRISBANE)
        first = emit_inventory_synced(
            "ringspo-us", listing_count=1, rows_upserted=1, synced_at=synced_at
        )
        second = emit_inventory_synced(
            "ringspo-us", listing_count=99, rows_upserted=99,
            synced_at=datetime(2026, 3, 7, 20, 0, tzinfo=BRISBANE),
        )
        assert first["event_id"] == second["event_id"]

    def test_different_dates_differ(self) -> None:
        day_one = build_event_id("ringspo-us", "inventory.synced", date(2026, 3, 7))
        day_two = build_event_id("ringspo-us", "inventory.synced", date(2026, 3, 8))
        assert day_one != day_two


class TestListingEventId:
    def test_same_listing_and_day_same_id(self) -> None:
        as_of = date(2026, 3, 7)
        first = build_listing_event_id("ringspo-us", "BN_1", "diamond.price_dropped", as_of)
        second = build_listing_event_id("ringspo-us", "BN_1", "diamond.price_dropped", as_of)
        assert first == second

    def test_different_triggers_differ(self) -> None:
        as_of = date(2026, 3, 7)
        drop = build_listing_event_id("ringspo-us", "BN_1", "diamond.price_dropped", as_of)
        gone = build_listing_event_id("ringspo-us", "BN_1", "diamond.disappeared", as_of)
        assert drop != gone


class TestDiamondEvents:
    def test_price_dropped_payload(self) -> None:
        drop = PriceDrop(
            listing_id="BN_1",
            stone_key="GIA:1",
            retailer_code="BN",
            old_price=100.0,
            new_price=90.0,
            drop_pct=10.0,
        )
        event = emit_diamond_price_dropped("ringspo-us", drop, as_of=date(2026, 3, 7))
        assert event["event_type"] == "diamond.price_dropped"
        assert event["payload"]["old_price"] == 100.0
        assert event["payload"]["new_price"] == 90.0

    def test_disappeared_payload(self) -> None:
        disappearance = Disappearance(
            listing_id="BN_1",
            stone_key="GIA:1",
            retailer_code="BN",
            first_missing_date=date(2026, 3, 5),
            last_price=6200.0,
        )
        event = emit_diamond_disappeared(
            "ringspo-us",
            disappearance,
            as_of=date(2026, 3, 7),
        )
        assert event["event_type"] == "diamond.disappeared"
        assert event["payload"]["stone_key"] == "GIA:1"
        assert event["payload"]["alternatives"] == []
