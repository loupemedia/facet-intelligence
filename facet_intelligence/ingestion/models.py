"""Canonical listing schema for tenant inventory (PRD-FI-001 Story 1.2)."""

from dataclasses import dataclass
from typing import Optional

DIAMOND_ITEM_TYPE = "diamond"

VALID_DIAMOND_TYPES = frozenset({"natural", "lab-grown"})
VALID_AVAILABILITY = frozenset({"in_stock", "out_of_stock", "unknown"})


@dataclass(frozen=True, slots=True)
class CanonicalListing:
    """One tenant inventory row after normalisation.

    ``listing_id`` is FI's diff key ({retailer}_{cert_or_sku}). ``stone_key`` maps
    to the consumer pipeline for engagement boundary joins.
    """

    listing_id: str
    stone_key: str
    retailer_code: str
    item_type: str = DIAMOND_ITEM_TYPE
    cert_lab: Optional[str] = None
    cert_number: Optional[str] = None
    retailer_diamond_id: Optional[str] = None
    diamond_type: Optional[str] = None
    shape: Optional[str] = None
    carat: Optional[float] = None
    color: Optional[str] = None
    clarity: Optional[str] = None
    cut: Optional[str] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    depth_mm: Optional[float] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    availability: str = "in_stock"
    product_url: Optional[str] = None
    image_url: Optional[str] = None
