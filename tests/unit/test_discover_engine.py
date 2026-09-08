"""Discover engine filters (Epic 3.4).

Test intent: discover filters apply budget, carat and diamond_type bounds before
ranking; buyer_intent is required.

Would fail if: a listing outside carat_max appeared in the filtered candidate set.
"""

import pytest

from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.recommend.discover import (
    _filter_discover_candidates,
    _resolve_rank_intent,
)


def _listing(
    listing_id: str,
    *,
    price: float = 5000,
    carat: float = 1.0,
    diamond_type: str = "natural",
    shape: str = "round",
    availability: str = "in_stock",
) -> CanonicalListing:
    return CanonicalListing(
        listing_id=listing_id,
        stone_key=f"GIA:{listing_id}",
        retailer_code="BN",
        price=price,
        carat=carat,
        diamond_type=diamond_type,
        shape=shape,
        availability=availability,
    )


class TestDiscoverFilters:
    def test_budget_max_excludes_expensive_stones(self) -> None:
        affordable = _listing("A", price=5000)
        expensive = _listing("B", price=9000)
        filtered = _filter_discover_candidates(
            [affordable, expensive],
            {"budget_max": 8000},
        )
        assert [listing.listing_id for listing in filtered] == ["A"]

    def test_budget_min_excludes_cheaper_stones(self) -> None:
        cheap = _listing("A", price=4000)
        premium = _listing("B", price=7000)
        filtered = _filter_discover_candidates(
            [cheap, premium],
            {"budget_min": 5000},
        )
        assert [listing.listing_id for listing in filtered] == ["B"]

    def test_carat_min_excludes_lighter_stones(self) -> None:
        small = _listing("A", carat=0.9)
        target = _listing("B", carat=1.0)
        filtered = _filter_discover_candidates(
            [small, target],
            {"carat_min": 1.0},
        )
        assert [listing.listing_id for listing in filtered] == ["B"]

    def test_carat_max_excludes_heavier_stones(self) -> None:
        small = _listing("A", carat=1.0)
        large = _listing("B", carat=1.5)
        filtered = _filter_discover_candidates(
            [small, large],
            {"carat_max": 1.2},
        )
        assert [listing.listing_id for listing in filtered] == ["A"]

    def test_shape_filter_normalizes_case(self) -> None:
        round_stone = _listing("A", shape="Round")
        oval = _listing("B", shape="oval")
        filtered = _filter_discover_candidates(
            [round_stone, oval],
            {"shape": "round"},
        )
        assert [listing.listing_id for listing in filtered] == ["A"]

    def test_diamond_type_filter(self) -> None:
        natural = _listing("A", diamond_type="natural")
        lab = _listing("B", diamond_type="lab-grown")
        filtered = _filter_discover_candidates(
            [natural, lab],
            {"diamond_type": "lab-grown"},
        )
        assert [listing.listing_id for listing in filtered] == ["B"]

    def test_in_stock_default_excludes_out_of_stock(self) -> None:
        available = _listing("A", availability="in_stock")
        gone = _listing("B", availability="out_of_stock")
        filtered = _filter_discover_candidates([available, gone], {})
        assert [listing.listing_id for listing in filtered] == ["A"]

    def test_in_stock_false_includes_out_of_stock(self) -> None:
        available = _listing("A", availability="in_stock")
        gone = _listing("B", availability="out_of_stock")
        filtered = _filter_discover_candidates(
            [available, gone],
            {"in_stock": False},
        )
        assert {listing.listing_id for listing in filtered} == {"A", "B"}


class TestResolveRankIntent:
    def test_buyer_intent_required(self) -> None:
        with pytest.raises(ValueError, match="buyer_intent is required"):
            _resolve_rank_intent({})

    def test_unsupported_buyer_intent_rejected(self) -> None:
        with pytest.raises(ValueError, match="Unsupported buyer_intent"):
            _resolve_rank_intent({"buyer_intent": "not_a_real_intent"})

    def test_deferred_buyer_intent_rejected(self) -> None:
        with pytest.raises(ValueError, match="not supported in v1"):
            _resolve_rank_intent({"buyer_intent": "safe_premium"})

    def test_category_overrides_buyer_intent(self) -> None:
        assert _resolve_rank_intent({"buyer_intent": "best_sparkle", "category": "good_value"}) == "good_value"

    def test_unsupported_category_rejected(self) -> None:
        with pytest.raises(ValueError, match="Unsupported category"):
            _resolve_rank_intent({"buyer_intent": "good_value", "category": "not_a_category"})

    def test_buyer_intent_used_when_category_absent(self) -> None:
        assert _resolve_rank_intent({"buyer_intent": "look_largest"}) == "look_largest"
