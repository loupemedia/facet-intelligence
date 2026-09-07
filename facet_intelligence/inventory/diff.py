"""Pure diff logic for disappearance (grace) and price-drop detection."""

from datetime import date
from typing import Mapping

from facet_intelligence.inventory.models import Disappearance, ListingState, PriceDrop

__all__ = [
    "detect_disappearances",
    "detect_price_drops",
]


def detect_disappearances(
    *,
    current: Mapping[str, ListingState],
    previous: Mapping[str, ListingState],
    miss_tracking: Mapping[str, date],
    as_of: date,
    grace_days: int,
) -> tuple[list[Disappearance], dict[str, date]]:
    """Detect listings absent from current inventory after grace days."""
    current_ids = set(current.keys())
    previous_ids = set(previous.keys())
    updated_tracking: dict[str, date] = {}
    disappeared: list[Disappearance] = []

    for listing_id, first_missing in miss_tracking.items():
        if listing_id in current_ids:
            continue
        days_missing = (as_of - first_missing).days + 1
        if days_missing >= grace_days:
            listing = previous.get(listing_id)
            if listing is not None:
                disappeared.append(
                    Disappearance(
                        listing_id=listing.listing_id,
                        stone_key=listing.stone_key,
                        retailer_code=listing.retailer_code,
                        first_missing_date=first_missing,
                        last_price=listing.price,
                        currency=listing.currency,
                        cert_lab=listing.cert_lab,
                        cert_number=listing.cert_number,
                        product_url=listing.product_url,
                    ),
                )
        else:
            updated_tracking[listing_id] = first_missing

    for listing_id in previous_ids - current_ids:
        if listing_id in current_ids or listing_id in miss_tracking:
            continue
        updated_tracking[listing_id] = as_of

    return disappeared, updated_tracking


def detect_price_drops(
    *,
    current: Mapping[str, ListingState],
    previous: Mapping[str, ListingState],
    min_drop_pct: float,
) -> list[PriceDrop]:
    """Find listings whose price fell by at least min_drop_pct vs previous snapshot."""
    drops: list[PriceDrop] = []
    for listing_id, current_listing in current.items():
        previous_listing = previous.get(listing_id)
        if previous_listing is None:
            continue
        if current_listing.price is None or previous_listing.price is None:
            continue
        if previous_listing.price <= 0:
            continue
        new_price = current_listing.price
        old_price = previous_listing.price
        if new_price >= old_price:
            continue
        drop_pct = ((old_price - new_price) / old_price) * 100.0
        if drop_pct < min_drop_pct:
            continue
        drops.append(
            PriceDrop(
                listing_id=listing_id,
                stone_key=current_listing.stone_key,
                retailer_code=current_listing.retailer_code,
                old_price=old_price,
                new_price=new_price,
                drop_pct=round(drop_pct, 2),
                currency=current_listing.currency,
                cert_lab=current_listing.cert_lab,
                cert_number=current_listing.cert_number,
                product_url=current_listing.product_url,
            ),
        )
    return drops
