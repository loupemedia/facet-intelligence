"""Recommendation categories and ranking."""

from enum import Enum
from typing import Callable

from facet_intelligence.recommend.models import ScoredCandidate

MAX_ALTERNATIVES = 5

GOOD_VALUE = "good_value"
LOOK_LARGEST = "look_largest"
BEST_SPARKLE = "best_sparkle"

VALID_CATEGORIES = frozenset({GOOD_VALUE, LOOK_LARGEST, BEST_SPARKLE})


class RecommendCategory(str, Enum):
    GOOD_VALUE = GOOD_VALUE
    LOOK_LARGEST = LOOK_LARGEST
    BEST_SPARKLE = BEST_SPARKLE


def _carat_key(candidate: ScoredCandidate) -> float:
    return candidate.listing.carat or 0.0


def _price_key(candidate: ScoredCandidate) -> float:
    return candidate.listing.price or float("inf")


def _composite_key(candidate: ScoredCandidate) -> float:
    return candidate.composite


_CATEGORY_SORT: dict[str, Callable[[ScoredCandidate], tuple]] = {
    GOOD_VALUE: lambda c: (_price_key(c), -_composite_key(c)),
    LOOK_LARGEST: lambda c: (-_carat_key(c), -c.composite, _price_key(c)),
    BEST_SPARKLE: lambda c: (-c.composite, -_carat_key(c), _price_key(c)),
}


def rank_candidates(
    candidates: list[ScoredCandidate],
    category: str,
    *,
    limit: int = MAX_ALTERNATIVES,
) -> list[ScoredCandidate]:
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Unsupported category {category!r}")
    sort_key = _CATEGORY_SORT[category]
    ordered = sorted(candidates, key=sort_key)
    return ordered[:limit]
