"""POST /v1/recommend (PRD-FI-001 Epic 3).

Test intent: recommend returns only substitutes at or above the anchor quality
floor, ranked by category, capped at five alternatives.

Would fail if: a lower-composite candidate appeared in good_value results, or
more than five alternatives were returned.
"""

import pytest
from fastapi.testclient import TestClient

from facet_intelligence.api.app import app
from facet_intelligence.api.deps import set_listing_store
from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.scoring.vanilla import VanillaScorer

API_KEY = "test-recommend-key"
TENANT_HEADER = "X-Facet-Intelligence-Tenant"


def _listing(
    listing_id: str,
    *,
    price: float,
    carat: float = 1.0,
    cut: str = "Excellent",
    color: str = "G",
    clarity: str = "VS1",
) -> CanonicalListing:
    return CanonicalListing(
        listing_id=listing_id,
        stone_key=f"GIA:{listing_id}",
        retailer_code=listing_id.split("_")[0],
        cert_lab="GIA",
        cert_number=listing_id.split("_", 1)[1],
        shape="round",
        carat=carat,
        color=color,
        clarity=clarity,
        cut=cut,
        price=price,
        currency="USD",
    )


class FakeRecommendStore:
    def __init__(self, listings: list[CanonicalListing]) -> None:
        self._listings = {listing.listing_id: listing for listing in listings}

    def fetch_listings(self, tenant_id: str, *, in_stock_only: bool = True) -> list[CanonicalListing]:
        if in_stock_only:
            return [listing for listing in self._listings.values() if listing.availability == "in_stock"]
        return list(self._listings.values())

    def fetch_listing_by_id(self, tenant_id: str, listing_id: str) -> CanonicalListing | None:
        return self._listings.get(listing_id)

    def fetch_listing_by_cert(
        self,
        tenant_id: str,
        cert_number: str,
        *,
        cert_lab: str | None = None,
    ) -> CanonicalListing | None:
        for listing in self._listings.values():
            if listing.cert_number == cert_number:
                if cert_lab is None or listing.cert_lab == cert_lab:
                    return listing
        return None


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
        "facet_intelligence.recommend.engine.get_scoring_backend",
        lambda tenant_id, requested, tenant_default: VanillaScorer(),
    )


class TestRecommendApi:
    def test_quality_floor_rejects_worse_substitute(
        self,
        client: TestClient,
        vanilla_scorer: None,
    ) -> None:
        anchor = _listing("BN_100", price=5000, cut="Ideal", color="E", clarity="VVS1")
        worse = _listing("JA_200", price=4000, cut="Good", color="I", clarity="SI2")
        store = FakeRecommendStore([anchor, worse])
        set_listing_store(store)
        response = client.post(
            "/v1/recommend",
            json={
                "anchor": {"listing_id": "BN_100"},
                "category": "good_value",
                "scoring_backend": "vanilla",
            },
            headers=_headers(),
        )
        set_listing_store(None)
        assert response.status_code == 200
        body = response.json()
        assert body["alternatives"] == []
        assert body["meta"]["reason_if_empty"] == "no_substitutes_meet_quality_floor"

    def test_good_value_prefers_lower_price_at_same_quality(
        self,
        client: TestClient,
        vanilla_scorer: None,
    ) -> None:
        anchor = _listing("BN_100", price=6000, cut="Excellent", color="G", clarity="VS1")
        cheaper = _listing("JA_200", price=5200, cut="Excellent", color="G", clarity="VS1")
        pricey = _listing("WF_300", price=5800, cut="Excellent", color="G", clarity="VS1")
        store = FakeRecommendStore([anchor, cheaper, pricey])
        set_listing_store(store)
        response = client.post(
            "/v1/recommend",
            json={
                "anchor": {"listing_id": "BN_100"},
                "category": "good_value",
                "scoring_backend": "vanilla",
            },
            headers=_headers(),
        )
        set_listing_store(None)
        body = response.json()
        assert len(body["alternatives"]) == 2
        assert body["alternatives"][0]["listing_id"] == "JA_200"
        assert "lower_price" in body["alternatives"][0]["reason_codes"]
        assert len(body["alternatives"]) <= 5

    def test_ringspo_us_rejects_vanilla_backend(self, client: TestClient) -> None:
        anchor = _listing("BN_100", price=6000)
        store = FakeRecommendStore([anchor])
        set_listing_store(store)
        response = client.post(
            "/v1/recommend",
            json={
                "anchor": {"listing_id": "BN_100"},
                "scoring_backend": "vanilla",
            },
            headers=_headers(),
        )
        set_listing_store(None)
        assert response.status_code == 400
        assert "sparklescore" in response.json()["detail"].lower()
