"""Inventory diff logic (PRD-FI-001 Epic 2).

Test intent: disappearance requires grace_days consecutive absences; price-drop
fires only when the drop percentage meets the configured floor.

Would fail if: a listing missing for one day emitted disappeared with grace=2,
or a 0.5% drop fired when min_drop_pct=1.0.
"""

from datetime import date

from facet_intelligence.inventory.diff import detect_disappearances, detect_price_drops
from facet_intelligence.inventory.models import ListingState


def _listing(listing_id: str, price: float | None = 100.0) -> ListingState:
    return ListingState(
        listing_id=listing_id,
        stone_key=f"GIA:{listing_id}",
        retailer_code="BN",
        price=price,
    )


class TestDisappearanceGrace:
    def test_one_day_missing_does_not_emit_with_grace_two(self) -> None:
        previous = {"A": _listing("A"), "B": _listing("B")}
        current = {"A": _listing("A")}
        disappeared, tracking = detect_disappearances(
            current=current,
            previous=previous,
            miss_tracking={},
            as_of=date(2026, 3, 7),
            grace_days=2,
        )
        assert disappeared == []
        assert tracking == {"B": date(2026, 3, 7)}

    def test_two_days_missing_emits_with_grace_two(self) -> None:
        previous = {"B": _listing("B")}
        current: dict[str, ListingState] = {}
        disappeared, tracking = detect_disappearances(
            current=current,
            previous=previous,
            miss_tracking={"B": date(2026, 3, 6)},
            as_of=date(2026, 3, 7),
            grace_days=2,
        )
        assert len(disappeared) == 1
        assert disappeared[0].listing_id == "B"
        assert tracking == {}

    def test_reappeared_listing_clears_tracking(self) -> None:
        previous = {"B": _listing("B")}
        current = {"B": _listing("B")}
        disappeared, tracking = detect_disappearances(
            current=current,
            previous=previous,
            miss_tracking={"B": date(2026, 3, 6)},
            as_of=date(2026, 3, 7),
            grace_days=2,
        )
        assert disappeared == []
        assert tracking == {}


class TestPriceDropDetection:
    def test_drop_below_threshold_ignored(self) -> None:
        previous = {"A": _listing("A", 100.0)}
        current = {"A": _listing("A", 99.5)}
        assert detect_price_drops(current=current, previous=previous, min_drop_pct=1.0) == []

    def test_drop_at_threshold_fires(self) -> None:
        previous = {"A": _listing("A", 100.0)}
        current = {"A": _listing("A", 98.0)}
        drops = detect_price_drops(current=current, previous=previous, min_drop_pct=1.0)
        assert len(drops) == 1
        assert drops[0].old_price == 100.0
        assert drops[0].new_price == 98.0
        assert drops[0].drop_pct == 2.0
