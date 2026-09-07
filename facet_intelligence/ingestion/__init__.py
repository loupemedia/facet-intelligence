"""Feed ingestion: raw rows → canonical listing schema."""

from facet_intelligence.ingestion.db_adapter import (
    dedupe_by_listing_id,
    load_country_market_listings,
    load_tenant_listings,
    map_stone_export_row,
    normalize_feed_rows,
)
from facet_intelligence.ingestion.feed_loader import load_feed, parse_feed_payload
from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.ingestion.normalize import build_listing_id, normalize_listing

__all__ = [
    "CanonicalListing",
    "build_listing_id",
    "dedupe_by_listing_id",
    "load_country_market_listings",
    "load_feed",
    "load_tenant_listings",
    "map_stone_export_row",
    "normalize_feed_rows",
    "normalize_listing",
    "parse_feed_payload",
]
