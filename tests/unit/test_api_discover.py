"""POST /v1/discover (PRD-FI-001 Epic 3.4).

Test intent: discover ranks in-stock inventory by buyer_intent with constraint
filters and returns at most five recommendations without an anchor.

Would fail if: best_sparkle discover returned a lower-composite stone first, or
more than five recommendations were returned.
"""

import pytest
from fastapi.testclient import TestClient

from facet_intelligence.api.app import app
from facet_intelligence.api.deps import set_listing_store
from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.scoring.vanilla import VanillaScorer

API_KEY = "test-discover-key"
TENANT_HEADER = "X-Facet-Intelligence-Tenant"


def _listing(
    listing_id: str,
    *,
    price: float,
    carat: float = 1.0,
    cut: str = "Excellent",
    color: str = "G",
    clarity: str = "VS1",
    shape: str = "round",
    diamond_type: str = "natural",
) -> CanonicalListing:
    return CanonicalListing(
        listing_id=listing_id,
        stone_key=f"GIA:{listing_id}",
        retailer_code=listing_id.split("_")[0],
        cert_lab="GIA",
        cert_number=listing_id.split("_", 1)[1],
        shape=shape,
        carat=carat,
        color=color,
        clarity=clarity,
        cut=cut,
        price=price,
        currency="USD",
        diamond_type=diamond_type,
    )


class FakeDiscoverStore:
    def __init__(self, listings: list[CanonicalListing]) -> None:
        self._listings = {listing.listing_id: listing for listing in listings}

    def fetch_listings(self, tenant_id: str, *, in_stock_only: bool = True) -> list[CanonicalListing]:
        if in_stock_only:
            return [listing for listing in self._listings.values() if listing.availability == "in_stock"]
        return list(self._listings.values())


@pytest.fixture(autouse=True)
def api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FACET_INTELLIGENCE_API_KEY", API_KEY)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {API_KEY}",
        TENANT_HEADER: "ringspo-us",
    }


@pytest.fixture
def vanilla_scorer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "facet_intelligence.recommend.discover.get_scoring_backend",
        lambda tenant_id, requested, tenant_default: VanillaScorer(),
    )


class TestDiscoverApi:
    def test_best_sparkle_ranks_highest_composite_first(
        self,
        client: TestClient,
        vanilla_scorer: None,
    ) -> None:
        high = _listing("BN_100", price=7000, cut="Ideal", color="E", clarity="VVS1")
        low = _listing("JA_200", price=6500, cut="Good", color="I", clarity="SI2")
        store = FakeDiscoverStore([high, low])
        set_listing_store(store)
        response = client.post(
            "/v1/discover",
            json={
                "buyer_intent": "best_sparkle",
                "constraints": {"budget_max": 8000},
                "scoring_backend": "vanilla",
            },
            headers=_headers(),
        )
        set_listing_store(None)
        assert response.status_code == 200
        body = response.json()
        assert len(body["recommendations"]) == 2
        assert body["recommendations"][0]["listing_id"] == "BN_100"
        assert "sparkle_ranked" in body["recommendations"][0]["reason_codes"]
        assert "top_ranked" in body["recommendations"][0]["reason_codes"]
        assert len(body["recommendations"]) <= 5

    def test_constraints_filter_budget_and_shape(
        self,
        client: TestClient,
        vanilla_scorer: None,
    ) -> None:
        in_budget = _listing("BN_100", price=7000, shape="round")
        over_budget = _listing("JA_200", price=9000, shape="round")
        wrong_shape = _listing("WF_300", price=6000, shape="oval")
        store = FakeDiscoverStore([in_budget, over_budget, wrong_shape])
        set_listing_store(store)
        response = client.post(
            "/v1/discover",
            json={
                "buyer_intent": "good_value",
                "constraints": {"budget_max": 8000, "shape": "round"},
                "scoring_backend": "vanilla",
            },
            headers=_headers(),
        )
        set_listing_store(None)
        body = response.json()
        assert [item["listing_id"] for item in body["recommendations"]] == ["BN_100"]
        assert body["meta"]["filtered_count"] == 1

    def test_empty_pool_returns_reason_if_empty(
        self,
        client: TestClient,
        vanilla_scorer: None,
    ) -> None:
        store = FakeDiscoverStore([_listing("BN_100", price=9000)])
        set_listing_store(store)
        response = client.post(
            "/v1/discover",
            json={
                "buyer_intent": "good_value",
                "constraints": {"budget_max": 5000},
                "scoring_backend": "vanilla",
            },
            headers=_headers(),
        )
        set_listing_store(None)
        body = response.json()
        assert body["recommendations"] == []
        assert body["meta"]["reason_if_empty"] == "no_candidates_after_filters"

    def test_deferred_buyer_intent_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/v1/discover",
            json={"buyer_intent": "lab_value"},
            headers=_headers(),
        )
        assert response.status_code == 400
        assert "not supported in v1" in response.json()["detail"]

    def test_ringspo_us_rejects_vanilla_backend(self, client: TestClient) -> None:
        store = FakeDiscoverStore([_listing("BN_100", price=6000)])
        set_listing_store(store)
        response = client.post(
            "/v1/discover",
            json={
                "buyer_intent": "good_value",
                "scoring_backend": "vanilla",
            },
            headers=_headers(),
        )
        set_listing_store(None)
        assert response.status_code == 400
        assert "sparklescore" in response.json()["detail"].lower()

    def test_category_overrides_ranking_intent(
        self,
        client: TestClient,
        vanilla_scorer: None,
    ) -> None:
        large_cheap = _listing("BN_100", price=5000, carat=1.5, cut="Good", color="H", clarity="SI1")
        small_bright = _listing("JA_200", price=6000, carat=1.0, cut="Ideal", color="E", clarity="VVS1")
        store = FakeDiscoverStore([large_cheap, small_bright])
        set_listing_store(store)
        response = client.post(
            "/v1/discover",
            json={
                "buyer_intent": "best_sparkle",
                "category": "look_largest",
                "scoring_backend": "vanilla",
            },
            headers=_headers(),
        )
        set_listing_store(None)
        body = response.json()
        assert body["recommendations"][0]["listing_id"] == "BN_100"
        assert body["meta"]["rank_by"] == "look_largest"
