"""Recommendation ranking (Epic 3).

Test intent: rank_candidates orders by category rules.

Would fail if: best_sparkle ranked a lower composite stone above a higher one.
"""

from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.recommend.categories import rank_candidates
from facet_intelligence.recommend.models import ScoredCandidate


def _candidate(listing_id: str, composite: float, price: float, carat: float) -> ScoredCandidate:
    listing = CanonicalListing(
        listing_id=listing_id,
        stone_key=f"GIA:{listing_id}",
        retailer_code="BN",
        carat=carat,
        price=price,
    )
    return ScoredCandidate(
        listing=listing,
        composite=composite,
        pillars={},
        scoring_backend="vanilla",
    )


class TestRankCandidates:
    def test_best_sparkle_orders_by_composite_desc(self) -> None:
        high = _candidate("A", 95.0, 6000, 1.0)
        low = _candidate("B", 88.0, 5000, 1.0)
        ranked = rank_candidates([low, high], "best_sparkle")
        assert ranked[0].listing.listing_id == "A"

    def test_good_value_prefers_lower_price_at_same_composite(self) -> None:
        cheap = _candidate("A", 90.0, 5000, 1.0)
        costly = _candidate("B", 90.0, 6000, 1.0)
        ranked = rank_candidates([costly, cheap], "good_value")
        assert ranked[0].listing.listing_id == "A"

    def test_look_largest_prefers_higher_carat(self) -> None:
        large = _candidate("A", 90.0, 6000, 1.5)
        small = _candidate("B", 92.0, 5000, 1.0)
        ranked = rank_candidates([small, large], "look_largest")
        assert ranked[0].listing.listing_id == "A"
