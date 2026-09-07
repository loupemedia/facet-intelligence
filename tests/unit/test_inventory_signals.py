"""Daily signal orchestration (PRD-FI-001 Epic 2).

Test intent: run_daily_inventory_signals compares live inventory to yesterday's
snapshot, emits events once, and always captures today's snapshot.

Would fail if: first run with no yesterday snapshot crashed instead of
capturing day-one snapshot, or duplicate event_id was delivered twice.
"""

from datetime import date

from facet_intelligence.inventory.models import ListingState
from facet_intelligence.inventory.signals import run_daily_inventory_signals


def _listing(listing_id: str, price: float) -> ListingState:
    return ListingState(
        listing_id=listing_id,
        stone_key=f"GIA:{listing_id}",
        retailer_code="BN",
        price=price,
    )


class FakeSnapshotStore:
    def __init__(self) -> None:
        self.live: dict[str, ListingState] = {}
        self.snapshots: dict[date, dict[str, ListingState]] = {}
        self.capture_calls: list[tuple[str, date]] = []

    def fetch_live_listings(self, tenant_id: str) -> dict[str, ListingState]:
        return dict(self.live)

    def fetch_snapshot(self, tenant_id: str, snapshot_date: date) -> dict[str, ListingState]:
        return dict(self.snapshots.get(snapshot_date, {}))

    def capture_snapshot(self, tenant_id: str, snapshot_date: date) -> int:
        self.capture_calls.append((tenant_id, snapshot_date))
        self.snapshots[snapshot_date] = dict(self.live)
        return len(self.live)


class FakeMissStore:
    def __init__(self) -> None:
        self.tracking: dict[str, date] = {}

    def load(self, tenant_id: str) -> dict[str, date]:
        return dict(self.tracking)

    def save(self, tenant_id: str, tracking: dict[str, date]) -> None:
        self.tracking = dict(tracking)


class FakeEventStore:
    def __init__(self) -> None:
        self.seen: set[str] = set()
        self.recorded: list[dict] = []

    def record_if_new(self, tenant_id: str, event: dict) -> bool:
        event_id = event["event_id"]
        if event_id in self.seen:
            return False
        self.seen.add(event_id)
        self.recorded.append(event)
        return True


class TestRunDailyInventorySignals:
    def test_first_run_skips_diff_and_captures_snapshot(self) -> None:
        snapshots = FakeSnapshotStore()
        snapshots.live = {"A": _listing("A", 100.0)}
        result = run_daily_inventory_signals(
            "ringspo-us",
            date(2026, 3, 7),
            snapshot_store=snapshots,
            miss_store=FakeMissStore(),
            event_store=FakeEventStore(),
            deliver_webhooks=False,
        )
        assert result.snapshot_rows == 1
        assert result.price_drops == 0
        assert result.disappearances == 0
        assert snapshots.capture_calls == [("ringspo-us", date(2026, 3, 7))]

    def test_price_drop_emitted_against_yesterday_snapshot(self) -> None:
        snapshots = FakeSnapshotStore()
        snapshots.snapshots[date(2026, 3, 6)] = {"A": _listing("A", 100.0)}
        snapshots.live = {"A": _listing("A", 90.0)}
        events = FakeEventStore()
        result = run_daily_inventory_signals(
            "ringspo-us",
            date(2026, 3, 7),
            snapshot_store=snapshots,
            miss_store=FakeMissStore(),
            event_store=events,
            deliver_webhooks=False,
        )
        assert result.price_drops == 1
        assert events.recorded[0]["event_type"] == "diamond.price_dropped"

    def test_duplicate_event_id_not_recorded_twice(self) -> None:
        snapshots = FakeSnapshotStore()
        snapshots.snapshots[date(2026, 3, 6)] = {"A": _listing("A", 100.0)}
        snapshots.live = {"A": _listing("A", 90.0)}
        events = FakeEventStore()
        run_daily_inventory_signals(
            "ringspo-us",
            date(2026, 3, 7),
            snapshot_store=snapshots,
            miss_store=FakeMissStore(),
            event_store=events,
            deliver_webhooks=False,
        )
        first_count = len(events.recorded)
        result = run_daily_inventory_signals(
            "ringspo-us",
            date(2026, 3, 7),
            snapshot_store=snapshots,
            miss_store=FakeMissStore(),
            event_store=events,
            deliver_webhooks=False,
        )
        assert len(events.recorded) == first_count
        assert result.events_skipped_duplicate == 1
