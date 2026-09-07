"""Listing store row mapping (PRD-FI-001 Story 1.4).

Test intent: upsert rows include tenant_id and every canonical listing field in
the order expected by tenant_listings INSERT.

Would fail if: listing_to_row omitted stone_key or mis-ordered columns relative
to LISTING_COLUMNS.
"""

from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.inventory.store import LISTING_COLUMNS, listing_to_row


class TestListingToRow:
    def test_row_matches_column_order(self) -> None:
        listing = CanonicalListing(
            listing_id="BN_2527938255",
            stone_key="GIA:2527938255",
            retailer_code="BN",
            cert_lab="GIA",
            cert_number="2527938255",
            carat=1.0,
            price=6200.0,
            currency="USD",
        )
        row = listing_to_row("ringspo-us", listing)
        assert len(row) == len(LISTING_COLUMNS)
        assert row[0] == "ringspo-us"
        assert row[1] == "BN_2527938255"
        assert row[2] == "GIA:2527938255"
        assert row[3] == "BN"
