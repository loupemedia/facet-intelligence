"""Country market retailer pools — mirrors diamond-prices policy subset."""

import os
from functools import lru_cache
from typing import List, Optional

import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTRY_MARKETS_PATH = os.path.join(PROJECT_ROOT, "config", "country_markets.yaml")


@lru_cache(maxsize=1)
def _load_doc() -> dict:
    with open(COUNTRY_MARKETS_PATH, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _normalise_country_code(country_code: str) -> str:
    return country_code.strip().lower()


def get_market(country_code: str) -> Optional[dict]:
    code = _normalise_country_code(country_code)
    return _load_doc().get("markets", {}).get(code)


def get_recommendation_retailer_slugs(country_code: str) -> List[str]:
    market = get_market(country_code)
    if market is None:
        return []
    return list(market.get("recommendation_retailers") or [])


def parse_inventory_source(inventory_source: str) -> tuple[str, str]:
    """Parse tenant inventory_source, e.g. ``country_market:us``."""
    if ":" not in inventory_source:
        raise ValueError(f"Invalid inventory_source {inventory_source!r}; expected kind:key")
    kind, key = inventory_source.split(":", 1)
    kind = kind.strip().lower()
    key = key.strip().lower()
    if not kind or not key:
        raise ValueError(f"Invalid inventory_source {inventory_source!r}; expected kind:key")
    return kind, key
