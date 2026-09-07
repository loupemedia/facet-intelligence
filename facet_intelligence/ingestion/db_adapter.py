"""Tenant inventory adapters — country market pool and stone-export rows."""

import logging
from typing import Any, Iterable, Mapping

from config.country_markets import parse_inventory_source
from config.retailers import get_retailer_codes_for_country, resolve_retailer_code
from config.tenants import TenantConfig, get_tenant
from facet_intelligence.ingestion.feed_loader import load_feed, parse_feed_payload
from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.ingestion.normalize import normalize_listing

logger = logging.getLogger(__name__)

__all__ = [
    "dedupe_by_listing_id",
    "load_country_market_listings",
    "load_tenant_listings",
    "map_stone_export_row",
    "normalize_feed_rows",
]


def map_stone_export_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Map R1 stone-layer export columns to normaliser input."""
    retailer_code = resolve_retailer_code(row)
    mapped: dict[str, Any] = dict(row)
    if retailer_code is not None:
        mapped["retailer_code"] = retailer_code

    if mapped.get("price_usd") is not None and mapped.get("price") is None:
        mapped["price"] = mapped["price_usd"]

    if mapped.get("vendor_url") is not None and mapped.get("product_url") is None:
        mapped["product_url"] = mapped["vendor_url"]

    diamond_type = mapped.get("diamond_type")
    if isinstance(diamond_type, str) and diamond_type.lower() == "lab-grown":
        mapped["diamond_type"] = "lab-grown"
    elif isinstance(diamond_type, str) and diamond_type.lower() in {"lab", "lab grown"}:
        mapped["diamond_type"] = "lab-grown"

    return mapped


def normalize_feed_rows(rows: Iterable[Mapping[str, Any]]) -> list[CanonicalListing]:
    """Normalise raw rows, skipping unidentifiable entries."""
    listings: list[CanonicalListing] = []
    for row in rows:
        listing = normalize_listing(row)
        if listing is not None:
            listings.append(listing)
    return listings


def dedupe_by_listing_id(listings: Iterable[CanonicalListing]) -> list[CanonicalListing]:
    """Keep one row per listing_id; later rows win (price updates)."""
    by_id: dict[str, CanonicalListing] = {}
    for listing in listings:
        by_id[listing.listing_id] = listing
    return list(by_id.values())


def load_country_market_listings(
    country_code: str,
    raw_rows: Iterable[Mapping[str, Any]],
    *,
    map_export: bool = False,
) -> list[CanonicalListing]:
    """Filter rows to a country's recommendation pool and normalise."""
    allowed_codes = get_retailer_codes_for_country(country_code)
    listings: list[CanonicalListing] = []

    for raw in raw_rows:
        row = map_stone_export_row(raw) if map_export else dict(raw)
        retailer_code = resolve_retailer_code(row)
        if retailer_code is None:
            logger.debug("Skipping row with unresolvable retailer: %r", raw)
            continue
        if retailer_code not in allowed_codes:
            logger.debug(
                "Skipping retailer %s; not in %s recommendation pool",
                retailer_code,
                country_code,
            )
            continue

        row["retailer_code"] = retailer_code
        listing = normalize_listing(row)
        if listing is not None:
            listings.append(listing)

    return dedupe_by_listing_id(listings)


def _load_for_country_market(tenant: TenantConfig, country_code: str, **kwargs) -> list[CanonicalListing]:
    source = kwargs.get("source", "json").lower()
    map_export = kwargs.get("map_export", source == "export")

    if kwargs.get("rows") is not None:
        raw_rows = kwargs["rows"]
    elif kwargs.get("path") is not None:
        feed_source = "json" if source == "export" else source
        raw_rows = load_feed(feed_source, kwargs["path"])
    elif kwargs.get("payload") is not None:
        raw_rows = list(parse_feed_payload(kwargs["payload"]))
    else:
        raise ValueError("Provide rows, path, or payload")

    return load_country_market_listings(country_code, raw_rows, map_export=map_export)


def load_tenant_listings(tenant_id: str, **kwargs) -> list[CanonicalListing]:
    """Load canonical listings for a tenant from feed data."""
    tenant = get_tenant(tenant_id)
    kind, key = parse_inventory_source(tenant["inventory_source"])

    if kind == "country_market":
        return _load_for_country_market(tenant, key, **kwargs)

    raise ValueError(f"Unsupported inventory_source kind {kind!r} for tenant {tenant_id}")
