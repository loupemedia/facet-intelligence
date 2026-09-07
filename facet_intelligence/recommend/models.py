"""Recommendation engine types."""

from dataclasses import dataclass
from typing import Any, Optional

from facet_intelligence.ingestion.models import CanonicalListing


@dataclass(frozen=True, slots=True)
class ScoredCandidate:
    listing: CanonicalListing
    composite: float
    pillars: dict[str, Any]
    scoring_backend: str


@dataclass(frozen=True, slots=True)
class ResolvedAnchor:
    listing: Optional[CanonicalListing]
    attributes: dict[str, Any]
    composite: Optional[float] = None
