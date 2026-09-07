"""POST /v1/inventory/sync (PRD-FI-001 Story 1.4).

Test intent: authenticated sync accepts in-pool listings for ringspo-us, persists
via the store, and returns 202 with inventory.synced event metadata.

Would fail if: missing auth returned 200, or out-of-pool RT rows were upserted.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from facet_intelligence.api.app import app
from facet_intelligence.api.deps import set_listing_store
from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.inventory.store import SyncStats

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
API_KEY = "test-sync-key"
TENANT_HEADER = "X-Facet-Intelligence-Tenant"


class FakeListingStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[CanonicalListing]]] = []

    def upsert_listings(self, tenant_id: str, listings):
        listing_list = list(listings)
        self.calls.append((tenant_id, listing_list))
        return SyncStats(
            tenant_id=tenant_id,
            listing_count=len(listing_list),
            rows_upserted=len(listing_list),
        )


@pytest.fixture(autouse=True)
def api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FACET_INTELLIGENCE_API_KEY", API_KEY)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def fake_store() -> FakeListingStore:
    store = FakeListingStore()
    set_listing_store(store)
    yield store
    set_listing_store(None)


def _auth_headers(tenant_id: str = "ringspo-us") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {API_KEY}",
        TENANT_HEADER: tenant_id,
    }


class TestInventorySyncAuth:
    def test_missing_auth_returns_401(self, client: TestClient, fake_store: FakeListingStore) -> None:
        response = client.post(
            "/v1/inventory/sync",
            json={"listings": []},
            headers={TENANT_HEADER: "ringspo-us"},
        )
        assert response.status_code == 401

    def test_unknown_tenant_returns_404(self, client: TestClient, fake_store: FakeListingStore) -> None:
        response = client.post(
            "/v1/inventory/sync",
            json={"listings": []},
            headers=_auth_headers("unknown-tenant"),
        )
        assert response.status_code == 404


class TestInventorySyncHappyPath:
    def test_sync_stone_export_returns_202(self, client: TestClient, fake_store: FakeListingStore) -> None:
        rows = json.loads((FIXTURES / "stone_export_us_sample.json").read_text(encoding="utf-8"))
        response = client.post(
            "/v1/inventory/sync",
            json={"source": "export", "listings": rows},
            headers=_auth_headers(),
        )
        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "accepted"
        assert body["tenant_id"] == "ringspo-us"
        assert body["listing_count"] == 2
        assert body["rows_upserted"] == 2
        assert len(body["event_id"]) == 32
        assert "synced_at" in body

        assert len(fake_store.calls) == 1
        tenant_id, listings = fake_store.calls[0]
        assert tenant_id == "ringspo-us"
        assert {listing.retailer_code for listing in listings} == {"JA", "BN"}

    def test_sync_json_payload_filters_out_of_pool(
        self,
        client: TestClient,
        fake_store: FakeListingStore,
    ) -> None:
        payload = json.loads((FIXTURES / "feed_us_json.json").read_text(encoding="utf-8"))
        response = client.post(
            "/v1/inventory/sync",
            json=payload,
            headers=_auth_headers(),
        )
        assert response.status_code == 202
        assert response.json()["listing_count"] == 1
        _, listings = fake_store.calls[0]
        assert listings[0].retailer_code == "BN"

    def test_missing_listings_returns_400(self, client: TestClient, fake_store: FakeListingStore) -> None:
        response = client.post(
            "/v1/inventory/sync",
            json={"source": "json"},
            headers=_auth_headers(),
        )
        assert response.status_code == 422
