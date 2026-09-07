"""Inventory signal domain models."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True, slots=True)
class ListingState:
    listing_id: str
    stone_key: str
    retailer_code: str
    price: Optional[float]
    currency: Optional[str] = None
    availability: str = "in_stock"
    cert_lab: Optional[str] = None
    cert_number: Optional[str] = None
    product_url: Optional[str] = None


@dataclass(frozen=True, slots=True)
class PriceDrop:
    listing_id: str
    stone_key: str
    retailer_code: str
    old_price: float
    new_price: float
    drop_pct: float
    currency: Optional[str] = None
    cert_lab: Optional[str] = None
    cert_number: Optional[str] = None
    product_url: Optional[str] = None


@dataclass(frozen=True, slots=True)
class Disappearance:
    listing_id: str
    stone_key: str
    retailer_code: str
    first_missing_date: date
    last_price: Optional[float]
    currency: Optional[str] = None
    cert_lab: Optional[str] = None
    cert_number: Optional[str] = None
    product_url: Optional[str] = None
