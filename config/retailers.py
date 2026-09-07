"""Retailer slug and display-name → code resolution."""

import os
from functools import lru_cache
from typing import Optional

import yaml

from config.country_markets import get_recommendation_retailer_slugs

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETAILERS_PATH = os.path.join(PROJECT_ROOT, "config", "retailers.yaml")


@lru_cache(maxsize=1)
def _load_doc() -> dict:
    with open(RETAILERS_PATH, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def get_retailer_entry(slug: str) -> Optional[dict]:
    return (_load_doc().get("retailers") or {}).get(slug)


def retailer_code_for_slug(slug: str) -> Optional[str]:
    entry = get_retailer_entry(slug)
    if entry is None:
        return None
    return entry.get("code")


def get_retailer_codes_for_country(country_code: str) -> frozenset[str]:
    codes = []
    for slug in get_recommendation_retailer_slugs(country_code):
        code = retailer_code_for_slug(slug)
        if code is None:
            raise KeyError(
                f"Country market retailer slug {slug!r} has no entry in config/retailers.yaml",
            )
        codes.append(code)
    return frozenset(codes)


def resolve_retailer_code(raw: dict) -> Optional[str]:
    """Resolve retailer code from a feed or stone-export row."""
    explicit = raw.get("retailer_code") or raw.get("retailerCode")
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip().upper()

    slug = raw.get("retailer_slug") or raw.get("retailer_key")
    if slug is not None:
        code = retailer_code_for_slug(str(slug).strip().lower())
        if code:
            return code

    display_name = raw.get("retailer") or raw.get("retailer_name")
    if display_name is not None:
        name_lower = str(display_name).strip().lower()
        for slug_key, entry in (_load_doc().get("retailers") or {}).items():
            if str(entry.get("name", "")).lower() == name_lower:
                return entry.get("code")
            if slug_key.replace("_", " ") == name_lower.replace("_", " "):
                return entry.get("code")

    return None
