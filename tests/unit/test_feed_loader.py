"""Feed loader and country-pool adapter (PRD-FI-001 Story 1.3).

Test intent: ringspo-us loads only US recommendation-pool retailers from CSV,
JSON, or stone-export rows; out-of-pool retailers are excluded.

Would fail if: Ritani rows were included in the US pool load, or CSV/JSON feeds
were not parsed into canonical listings.
"""

import json
import pathlib

from facet_intelligence.ingestion.db_adapter import (
    dedupe_by_listing_id,
    load_country_market_listings,
    load_tenant_listings,
    map_stone_export_row,
)
from facet_intelligence.ingestion.feed_loader import load_feed, load_json_rows
from facet_intelligence.ingestion.models import CanonicalListing

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures"


class TestFeedLoader:
    def test_load_csv_fixture(self) -> None:
        rows = load_feed("csv", FIXTURES / "feed_us_sample.csv")
        assert len(rows) == 3
        assert rows[0]["retailer"] == "James Allen"

    def test_load_json_fixture(self) -> None:
        rows = load_json_rows((FIXTURES / "feed_us_json.json").read_text(encoding="utf-8"))
        assert len(rows) == 2
        assert rows[0]["retailer_code"] == "BN"


class TestCountryPoolAdapter:
    def test_stone_export_maps_display_name_to_code(self) -> None:
        row = {
            "retailer": "James Allen",
            "price": 1000,
            "vendor_url": "https://example.com/x",
        }
        mapped = map_stone_export_row(row)
        assert mapped["retailer_code"] == "JA"
        assert mapped["product_url"] == "https://example.com/x"

    def test_country_pool_excludes_out_of_pool_retailer(self) -> None:
        rows = json.loads((FIXTURES / "stone_export_us_sample.json").read_text(encoding="utf-8"))
        listings = load_country_market_listings("us", rows, map_export=True)
        retailer_codes = {listing.retailer_code for listing in listings}
        assert retailer_codes == {"JA", "BN"}
        assert "RT" not in retailer_codes

    def test_same_cert_two_retailers_in_pool(self) -> None:
        rows = json.loads((FIXTURES / "stone_export_us_sample.json").read_text(encoding="utf-8"))
        listings = load_country_market_listings("us", rows, map_export=True)
        by_retailer = {listing.retailer_code: listing for listing in listings}
        assert by_retailer["JA"].stone_key == by_retailer["BN"].stone_key
        assert by_retailer["JA"].listing_id != by_retailer["BN"].listing_id


class TestRingspoUsTenantLoader:
    def test_load_from_csv_path(self) -> None:
        listings = load_tenant_listings(
            "ringspo-us",
            source="csv",
            path=FIXTURES / "feed_us_sample.csv",
            map_export=True,
        )
        assert len(listings) == 2
        assert {listing.retailer_code for listing in listings} == {"JA", "BN"}

    def test_load_from_json_payload(self) -> None:
        payload = json.loads((FIXTURES / "feed_us_json.json").read_text(encoding="utf-8"))
        listings = load_tenant_listings("ringspo-us", source="json", payload=payload)
        assert len(listings) == 1
        assert listings[0].retailer_code == "BN"

    def test_load_from_stone_export_rows(self) -> None:
        rows = json.loads((FIXTURES / "stone_export_us_sample.json").read_text(encoding="utf-8"))
        listings = load_tenant_listings(
            "ringspo-us",
            source="export",
            rows=rows,
        )
        assert len(listings) == 2


class TestDedupeByListingId:
    def test_later_row_wins(self) -> None:
        first = CanonicalListing(
            listing_id="BN_1",
            stone_key="GIA:1",
            retailer_code="BN",
            price=1000.0,
        )
        second = CanonicalListing(
            listing_id="BN_1",
            stone_key="GIA:1",
            retailer_code="BN",
            price=900.0,
        )
        deduped = dedupe_by_listing_id([first, second])
        assert len(deduped) == 1
        assert deduped[0].price == 900.0
