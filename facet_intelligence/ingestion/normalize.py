"""Raw feed rows → canonical listing schema + stable tenant listing_id."""

import logging
from typing import Any, Mapping, Optional

from facet_intelligence.ingestion.measurements import parse_measurements
from facet_intelligence.ingestion.models import (
    VALID_AVAILABILITY,
    VALID_DIAMOND_TYPES,
    CanonicalListing,
    DIAMOND_ITEM_TYPE,
)
from facet_intelligence.ingestion.stone_key import (
    build_stone_key,
    normalise_cert_lab,
    normalise_cert_number,
)

logger = logging.getLogger(__name__)

_NULL_TOKENS = frozenset({"", "nan", "none", "null", "n/a", "na", "-", "--"})

__all__ = [
    "build_listing_id",
    "normalize_listing",
]


def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in _NULL_TOKENS else text


def _first(raw: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return None


def _to_float(value: Any, places: int) -> Optional[float]:
    text = _clean(value)
    if text is None:
        return None
    try:
        return round(float(text), places)
    except (TypeError, ValueError):
        return None


def build_listing_id(
    *,
    retailer_code: str,
    cert_number: Any = None,
    retailer_diamond_id: Any = None,
) -> Optional[str]:
    """Stable FI tenant listing_id for day-over-day diff.

    Format: ``{retailer_code}_{identifier}`` where identifier is normalised
    cert_number first, then retailer SKU. Matches market_intel M1 hierarchy;
    this is homonym #3 in stone-identity-keys.md, not consumer stone_key.
    """
    number = normalise_cert_number(cert_number)
    if number:
        return f"{retailer_code}_{number}"

    sku = _clean(retailer_diamond_id)
    if sku:
        return f"{retailer_code}_{sku}"

    return None


def _resolve_dimensions(raw: Mapping[str, Any]) -> tuple[Optional[float], Optional[float], Optional[float]]:
    length = _to_float(_first(raw, "length_mm", "length"), 3)
    width = _to_float(_first(raw, "width_mm", "width"), 3)
    depth = _to_float(_first(raw, "depth_mm", "depth"), 3)

    if length is not None and width is not None and depth is not None:
        return length, width, depth

    parsed_length, parsed_width, parsed_depth = parse_measurements(
        _first(raw, "measurements_mm", "measurements"),
    )
    return (
        length if length is not None else parsed_length,
        width if width is not None else parsed_width,
        depth if depth is not None else parsed_depth,
    )


def _resolve_availability(raw: Mapping[str, Any]) -> str:
    token = (_clean(_first(raw, "availability")) or "in_stock").lower()
    if token in VALID_AVAILABILITY:
        return token
    if token in {"available", "yes", "true", "1"}:
        return "in_stock"
    if token in {"unavailable", "no", "false", "0", "sold"}:
        return "out_of_stock"
    logger.warning("Unknown availability %r; defaulting to unknown", token)
    return "unknown"


def normalize_listing(raw: Mapping[str, Any]) -> Optional[CanonicalListing]:
    """Normalise one raw feed row to a canonical listing, or None if unidentifiable."""
    retailer_code = _clean(_first(raw, "retailer_code", "retailer"))
    if not retailer_code:
        logger.debug("Skipping row with no retailer_code: %r", raw)
        return None

    item_type = (_clean(_first(raw, "item_type")) or DIAMOND_ITEM_TYPE).lower()
    if item_type != DIAMOND_ITEM_TYPE:
        logger.debug("Skipping non-diamond item_type %r", item_type)
        return None

    cert_lab_raw = _first(raw, "cert_lab", "cert_lab_name", "lab")
    cert_number_raw = _first(raw, "cert_number", "cert", "certificate_number")
    retailer_diamond_id = _clean(_first(raw, "retailer_diamond_id", "sku", "merchant_sku"))

    listing_id = build_listing_id(
        retailer_code=retailer_code,
        cert_number=cert_number_raw,
        retailer_diamond_id=retailer_diamond_id,
    )

    cert_lab = normalise_cert_lab(cert_lab_raw)
    cert_number = normalise_cert_number(cert_number_raw)
    if not (cert_lab and cert_number):
        cert_lab = cert_number = None
    if listing_id is None:
        logger.debug("Skipping row with no listing_id for retailer %s", retailer_code)
        return None

    length_mm, width_mm, depth_mm = _resolve_dimensions(raw)

    diamond_type = _clean(_first(raw, "diamond_type", "type"))
    if diamond_type == "lab":
        diamond_type = "lab-grown"
    if diamond_type is not None and diamond_type not in VALID_DIAMOND_TYPES:
        logger.warning("Unknown diamond_type %r; clearing", diamond_type)
        diamond_type = None

    stone_key = build_stone_key(
        retailer_code=retailer_code,
        cert_lab=cert_lab,
        cert_number=cert_number,
        retailer_diamond_id=retailer_diamond_id,
        shape=_first(raw, "shape"),
        carat=_first(raw, "carat"),
        length_mm=length_mm,
        width_mm=width_mm,
        depth_mm=depth_mm,
    )

    return CanonicalListing(
        listing_id=listing_id,
        stone_key=stone_key,
        retailer_code=retailer_code,
        item_type=item_type,
        cert_lab=cert_lab,
        cert_number=cert_number,
        retailer_diamond_id=retailer_diamond_id,
        diamond_type=diamond_type,
        shape=_clean(_first(raw, "shape")),
        carat=_to_float(_first(raw, "carat"), 2),
        color=_clean(_first(raw, "color", "colour")),
        clarity=_clean(_first(raw, "clarity")),
        cut=_clean(_first(raw, "cut", "cut_grade")),
        length_mm=length_mm,
        width_mm=width_mm,
        depth_mm=depth_mm,
        price=_to_float(_first(raw, "price", "price_usd"), 2),
        currency=_clean(_first(raw, "currency")) or "USD",
        availability=_resolve_availability(raw),
        product_url=_clean(_first(raw, "product_url", "url")),
        image_url=_clean(_first(raw, "image_url", "image")),
    )
