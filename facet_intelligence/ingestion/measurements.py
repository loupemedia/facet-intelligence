"""Parse retailer measurement strings into millimetre dimensions."""

import re
from typing import Any, Optional, Tuple

_NUMBER = re.compile(r"\d+(?:\.\d+)?")

_NULL_TOKENS = frozenset({"", "nan", "none", "null", "n/a", "na", "-", "--"})

MIN_PLAUSIBLE_MM = 0.5
MAX_PLAUSIBLE_MM = 100.0

Dimensions = Tuple[Optional[float], Optional[float], Optional[float]]


def _plausible(value: float) -> bool:
    return MIN_PLAUSIBLE_MM <= value <= MAX_PLAUSIBLE_MM


def parse_measurements(raw: Any) -> Dimensions:
    """Return ``(length_mm, width_mm, depth_mm)``, or Nones if unparseable."""
    if raw is None:
        return (None, None, None)

    text = str(raw).strip()
    if text.lower() in _NULL_TOKENS:
        return (None, None, None)

    numbers = [float(match) for match in _NUMBER.findall(text)]
    if len(numbers) != 3:
        return (None, None, None)

    if not all(_plausible(number) for number in numbers):
        return (None, None, None)

    length, width, depth = numbers
    return (length, width, depth)
