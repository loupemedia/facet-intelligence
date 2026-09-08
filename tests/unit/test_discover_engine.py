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
) -> CanonicalListing:
    return CanonicalListing(
        listing_id=listing_id,
        stone_key=f"GIA:{listing_id}",
        retailer_code="BN",
        price=price,
        carat=carat,
        diamond_type=diamond_type,
        shape=shape,
    )


class TestDiscoverFilters:
    def test_carat_max_excludes_heavier_stones(self) -> None:
        small = _listing("A", carat=1.0)
        large = _listing("B", carat=1.5)
        filtered = _filter_discover_candidates(
            [small, large],
            {"carat_max": 1.2},
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


class TestResolveRankIntent:
    def test_buyer_intent_required(self) -> None:
        with pytest.raises(ValueError, match="buyer_intent is required"):
            _resolve_rank_intent({})

    def test_category_overrides_buyer_intent(self) -> None:
        assert _resolve_rank_intent({"buyer_intent": "best_sparkle", "category": "good_value"}) == "good_value"
