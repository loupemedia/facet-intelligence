"""Discover engine filters (Epic 3.4).

Test intent: discover filters apply budget, carat and diamond_type bounds before
ranking; buyer_intent is required; SparkleScore is called for at most
DISCOVER_SCORE_CAP listings after those filters.

Would fail if: a listing outside carat_max appeared in the filtered candidate
set, or a 28-listing pool produced 28 score_listing calls.
"""

import pytest

from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.recommend.discover import (
    DISCOVER_SCORE_CAP,
    _filter_discover_candidates,
    _preselect_for_scoring,
    _resolve_rank_intent,
    discover_listings,
)
from facet_intelligence.scoring.vanilla import VanillaScorer


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


class CountingScorer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def score_listing(self, listing: CanonicalListing, tenant_id: str) -> dict:
        self.calls.append(listing.listing_id)
        return {"composite": 50.0, "pillars": {}}


class FakeDiscoverStore:
    def __init__(self, listings: list[CanonicalListing]) -> None:
        self._listings = list(listings)

    def fetch_listings(self, tenant_id: str, *, in_stock_only: bool = True) -> list[CanonicalListing]:
        if in_stock_only:
            return [listing for listing in self._listings if listing.availability == "in_stock"]
        return list(self._listings)


class TestDiscoverScoreCap:
    def test_preselect_keeps_cheapest_for_good_value(self) -> None:
        listings = [_listing(f"S{i}", price=float(1000 + i)) for i in range(DISCOVER_SCORE_CAP + 5)]
        selected = _preselect_for_scoring(listings, "good_value")
        assert len(selected) == DISCOVER_SCORE_CAP
        assert [listing.listing_id for listing in selected] == [
            f"S{i}" for i in range(DISCOVER_SCORE_CAP)
        ]

    def test_sparklescore_path_scores_at_most_cap(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scorer = CountingScorer()
        monkeypatch.setattr(
            "facet_intelligence.recommend.discover.get_scoring_backend",
            lambda tenant_id, requested, tenant_default: scorer,
        )
        listings = [
            _listing(f"S{i}", price=float(1000 + i), carat=1.0)
            for i in range(DISCOVER_SCORE_CAP + 8)
        ]
        result = discover_listings(
            "ringspo-us",
            {"buyer_intent": "good_value", "constraints": {}},
            store=FakeDiscoverStore(listings),
        )
        assert len(scorer.calls) == DISCOVER_SCORE_CAP
        assert result.meta["scored_count"] == DISCOVER_SCORE_CAP
        assert result.meta["score_cap"] == DISCOVER_SCORE_CAP
        assert result.meta["filtered_count"] == DISCOVER_SCORE_CAP + 8

    def test_under_cap_scores_every_filtered_listing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scorer = CountingScorer()
        monkeypatch.setattr(
            "facet_intelligence.recommend.discover.get_scoring_backend",
            lambda tenant_id, requested, tenant_default: scorer,
        )
        listings = [_listing("A", price=5000), _listing("B", price=6000)]
        result = discover_listings(
            "ringspo-us",
            {"buyer_intent": "good_value"},
            store=FakeDiscoverStore(listings),
        )
        assert scorer.calls == ["A", "B"]
        assert result.meta["scored_count"] == 2
        assert "score_cap" not in result.meta

    def test_vanilla_backend_still_ranks_without_score_listing_calls(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "facet_intelligence.recommend.discover.get_scoring_backend",
            lambda tenant_id, requested, tenant_default: VanillaScorer(),
        )
        listings = [_listing(f"S{i}", price=float(2000 + i)) for i in range(DISCOVER_SCORE_CAP + 3)]
        result = discover_listings(
            "ringspo-us",
            {"buyer_intent": "good_value", "scoring_backend": "vanilla"},
            store=FakeDiscoverStore(listings),
        )
        assert len(result.recommendations) == 5
        assert result.meta["scored_count"] == DISCOVER_SCORE_CAP

