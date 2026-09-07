"""Consumer stone_key resolution for engagement boundary mapping.

FI persists and diffs on tenant-scoped ``listing_id`` ({retailer}_{cert_or_sku}).
Engagement watches use ``stone_key`` (e.g. ``GIA:2527938255``) without a retailer
prefix. Logic mirrors ``diamond-prices/shared/stones/identity.py``; this repo does
not import across that boundary.

Cross-pipeline rules: ``diamond-prices/docs/architecture/stone-identity-keys.md``.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CERT_LAB_ALIASES = {
    "GIA": "GIA",
    "GEMOLOGICALINSTITUTEOFAMERICA": "GIA",
    "IGI": "IGI",
    "INTERNATIONALGEMOLOGICALINSTITUTE": "IGI",
    "AGS": "AGS",
    "AGSL": "AGS",
    "AMERICANGEMSOCIETY": "AGS",
    "HRD": "HRD",
    "HRDANTWERP": "HRD",
    "GCAL": "GCAL",
    "EGL": "EGL",
}

_NULL_TOKENS = frozenset({"", "nan", "none", "null", "n/a", "na", "-", "--"})

__all__ = [
    "build_stone_key",
    "normalise_cert_lab",
    "normalise_cert_number",
]


def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in _NULL_TOKENS else text


def normalise_cert_lab(raw: Any) -> Optional[str]:
    """Canonical lab name, or None when absent."""
    text = _clean(raw)
    if text is None:
        return None

    squashed = "".join(ch for ch in text.upper() if ch.isalnum())
    if not squashed:
        return None

    canonical = _CERT_LAB_ALIASES.get(squashed)
    if canonical is None:
        logger.warning("Unrecognised cert lab %r (normalised %r)", text, squashed)
        return squashed
    return canonical


def normalise_cert_number(raw: Any) -> Optional[str]:
    """Certificate number as a bare string, or None when absent."""
    text = _clean(raw)
    if text is None:
        return None

    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]

    return "".join(text.split()).replace("-", "") or None


def _fingerprint_number(value: Any, places: int) -> str:
    text = _clean(value)
    if text is None:
        return ""
    try:
        return f"{float(text):.{places}f}"
    except (TypeError, ValueError):
        return text.lower()


def build_stone_key(
    *,
    retailer_code: str,
    cert_lab: Any = None,
    cert_number: Any = None,
    retailer_diamond_id: Any = None,
    shape: Any = None,
    carat: Any = None,
    length_mm: Any = None,
    width_mm: Any = None,
    depth_mm: Any = None,
) -> str:
    """Resolve one physical diamond to one consumer stone_key."""
    lab = normalise_cert_lab(cert_lab)
    number = normalise_cert_number(cert_number)
    if lab and number:
        return f"{lab}:{number}"

    sku = _clean(retailer_diamond_id)
    if sku:
        return f"{retailer_code}#{sku}"

    shape_token = (_clean(shape) or "").lower()
    return "|".join((
        retailer_code,
        shape_token,
        _fingerprint_number(carat, 2),
        _fingerprint_number(length_mm, 2),
        _fingerprint_number(width_mm, 2),
        _fingerprint_number(depth_mm, 2),
    ))
