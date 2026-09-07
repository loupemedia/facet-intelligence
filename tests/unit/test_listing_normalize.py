"""Listing normalisation (PRD-FI-001 Story 1.2).

Test intent: FI persists and diffs on tenant-scoped listing_id, but every canonical
listing must also resolve a stone_key for engagement boundary joins.

Would fail if: the same GIA cert at Blue Nile and James Allen produced one
listing_id, or if stone_key carried a retailer prefix for certed stones.
"""

import json
import pathlib

import pytest

from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.ingestion.normalize import build_listing_id, normalize_listing
from facet_intelligence.ingestion.stone_key import (
    build_stone_key,
    normalise_cert_lab,
    normalise_cert_number,
)

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class TestCertNormalisation:
    @pytest.mark.parametrize("raw", ["GIA", "gia", "G.I.A.", " GIA "])
    def test_gia_variants_collapse(self, raw: str) -> None:
        assert normalise_cert_lab(raw) == "GIA"

    def test_cert_number_strips_float_formatting(self) -> None:
        assert normalise_cert_number("2527938255.0") == "2527938255"

    def test_cert_number_strips_spaces_and_hyphens(self) -> None:
        assert normalise_cert_number("2527 938-255") == "2527938255"


class TestBuildListingId:
    def test_cert_number_preferred_over_sku(self) -> None:
        listing_id = build_listing_id(
            retailer_code="BN",
            cert_number="2527938255",
            retailer_diamond_id="SKU-1",
        )
        assert listing_id == "BN_2527938255"

    def test_sku_fallback_when_no_cert(self) -> None:
        listing_id = build_listing_id(
            retailer_code="BE",
            retailer_diamond_id="BE-111",
        )
        assert listing_id == "BE_BE-111"

    def test_returns_none_without_identifier(self) -> None:
        assert build_listing_id(retailer_code="BN") is None


class TestStoneKey:
    def test_same_cert_at_two_retailers_gives_one_stone_key(self) -> None:
        bn = build_stone_key(
            retailer_code="BN",
            cert_lab="GIA",
            cert_number="2527938255",
        )
        ja = build_stone_key(
            retailer_code="JA",
            cert_lab="gia",
            cert_number="2527938255.0",
        )
        assert bn == ja == "GIA:2527938255"

    def test_stone_key_has_no_retailer_prefix_for_certed_stones(self) -> None:
        key = build_stone_key(
            retailer_code="BN",
            cert_lab="GIA",
            cert_number="123",
        )
        assert not key.startswith("BN_")
        assert key == "GIA:123"


class TestNormalizeListingFromFixtures:
    def test_certed_blue_nile_fixture(self) -> None:
        listing = normalize_listing(_load_fixture("listing_certed_bn.json"))
        assert listing is not None
        assert listing.listing_id == "BN_2527938255"
        assert listing.stone_key == "GIA:2527938255"
        assert listing.retailer_code == "BN"
        assert listing.carat == 1.0
        assert listing.length_mm == 6.5
        assert listing.availability == "in_stock"

    def test_same_cert_different_retailers_have_distinct_listing_ids(self) -> None:
        bn = normalize_listing(_load_fixture("listing_certed_bn.json"))
        ja = normalize_listing(_load_fixture("listing_certed_ja_same_cert.json"))
        assert bn is not None and ja is not None
        assert bn.listing_id == "BN_2527938255"
        assert ja.listing_id == "JA_2527938255"
        assert bn.listing_id != ja.listing_id
        assert bn.stone_key == ja.stone_key == "GIA:2527938255"

    def test_uncerted_sku_fixture(self) -> None:
        listing = normalize_listing(_load_fixture("listing_uncerted_sku.json"))
        assert listing is not None
        assert listing.listing_id == "BE_BE-111"
        assert listing.stone_key == "BE#BE-111"
        assert listing.cert_lab is None
        assert listing.cert_number is None

    def test_fingerprint_only_without_sku_is_rejected(self) -> None:
        """No cert or SKU means no stable listing_id for day-over-day diff."""
        row = _load_fixture("listing_fingerprint_only.json")
        row["retailer_code"] = "BE"
        assert normalize_listing(row) is None

    def test_missing_retailer_is_rejected(self) -> None:
        assert normalize_listing(_load_fixture("listing_missing_retailer.json")) is None


class TestListingIdVsStoneKeyBoundary:
    def test_canonical_listing_carries_both_keys(self) -> None:
        listing = normalize_listing(_load_fixture("listing_certed_bn.json"))
        assert listing is not None
        assert listing.listing_id.startswith("BN_")
        assert listing.stone_key.startswith("GIA:")
        assert listing.listing_id != listing.stone_key

    def test_listing_id_matches_market_intel_shape_not_stone_key(self) -> None:
        """Homonym guard: FI listing_id is retailer-scoped like M1, not GIA:cert."""
        listing = normalize_listing(_load_fixture("listing_certed_bn.json"))
        assert listing is not None
        assert listing.listing_id == "BN_2527938255"
        assert listing.stone_key == "GIA:2527938255"

    def test_frozen_dataclass(self) -> None:
        listing = normalize_listing(_load_fixture("listing_certed_bn.json"))
        assert listing is not None
        assert isinstance(listing, CanonicalListing)
        with pytest.raises(AttributeError):
            listing.listing_id = "changed"  # type: ignore[misc]
