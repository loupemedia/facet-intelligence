"""Resolve recommend anchors from listing_id, cert, or attributes."""

from typing import Any, Mapping, Optional

from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.ingestion.stone_key import normalise_cert_lab, normalise_cert_number
from facet_intelligence.inventory.store import ListingStore
from facet_intelligence.recommend.models import ResolvedAnchor

__all__ = [
    "resolve_anchor",
]


def _listing_to_attributes(listing: CanonicalListing) -> dict[str, Any]:
    return {
        "listing_id": listing.listing_id,
        "stone_key": listing.stone_key,
        "retailer_code": listing.retailer_code,
        "cert_lab": listing.cert_lab,
        "cert_number": listing.cert_number,
        "shape": listing.shape,
        "carat": listing.carat,
        "color": listing.color,
        "clarity": listing.clarity,
        "cut": listing.cut,
        "diamond_type": listing.diamond_type,
        "price": listing.price,
        "length_mm": listing.length_mm,
        "width_mm": listing.width_mm,
        "depth_mm": listing.depth_mm,
    }


def resolve_anchor(
    tenant_id: str,
    anchor_body: Mapping[str, Any],
    *,
    store: Optional[ListingStore] = None,
) -> ResolvedAnchor:
    listing_store = store or ListingStore()

    if "listing_id" in anchor_body and anchor_body["listing_id"]:
        listing = listing_store.fetch_listing_by_id(tenant_id, str(anchor_body["listing_id"]))
        if listing is None:
            raise ValueError(f"Unknown anchor listing_id for tenant {tenant_id}")
        return ResolvedAnchor(listing=listing, attributes=_listing_to_attributes(listing))

    if "cert" in anchor_body and anchor_body["cert"]:
        cert_payload = anchor_body["cert"]
        if isinstance(cert_payload, str):
            cert_number = normalise_cert_number(cert_payload)
            cert_lab = normalise_cert_lab(anchor_body.get("cert_lab"))
        elif isinstance(cert_payload, Mapping):
            cert_number = normalise_cert_number(cert_payload.get("cert_number") or cert_payload.get("number"))
            cert_lab = normalise_cert_lab(cert_payload.get("cert_lab") or cert_payload.get("lab"))
        else:
            raise ValueError("anchor.cert must be a string or object")
        if not cert_number:
            raise ValueError("anchor.cert requires a cert number")
        listing = listing_store.fetch_listing_by_cert(tenant_id, cert_number, cert_lab=cert_lab)
        if listing is None:
            raise ValueError(f"No in-stock listing for cert {cert_lab}:{cert_number}")
        return ResolvedAnchor(listing=listing, attributes=_listing_to_attributes(listing))

    if "attributes" in anchor_body and anchor_body["attributes"]:
        attributes = dict(anchor_body["attributes"])
        return ResolvedAnchor(listing=None, attributes=attributes)

    raise ValueError("anchor must include listing_id, cert, or attributes")
