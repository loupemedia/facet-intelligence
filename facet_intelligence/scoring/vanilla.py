"""Vanilla scoring backend — structured 4Cs heuristic for B2B tenants."""

from typing import Any

from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.scoring.backend import ScoringBackend

_CUT_SCORES = {
    "excellent": 95.0,
    "ideal": 98.0,
    "very good": 82.0,
    "good": 72.0,
    "fair": 60.0,
    "poor": 45.0,
}

_COLOR_SCORES = {
    "d": 98.0,
    "e": 96.0,
    "f": 94.0,
    "g": 90.0,
    "h": 85.0,
    "i": 78.0,
    "j": 70.0,
}

_CLARITY_SCORES = {
    "fl": 99.0,
    "if": 97.0,
    "vvs1": 94.0,
    "vvs2": 92.0,
    "vs1": 88.0,
    "vs2": 84.0,
    "si1": 76.0,
    "si2": 68.0,
    "i1": 58.0,
}


def _grade_score(raw: Any, table: dict[str, float], default: float = 75.0) -> float:
    if raw is None:
        return default
    token = str(raw).strip().lower()
    return table.get(token, default)


def _listing_attributes(listing: CanonicalListing | dict[str, Any]) -> dict[str, Any]:
    if isinstance(listing, CanonicalListing):
        return {
            "cut": listing.cut,
            "color": listing.color,
            "clarity": listing.clarity,
            "carat": listing.carat,
            "price": listing.price,
        }
    return dict(listing)


def vanilla_composite(attributes: dict[str, Any]) -> tuple[float, dict[str, float]]:
    cut = _grade_score(attributes.get("cut"), _CUT_SCORES)
    color = _grade_score(attributes.get("color"), _COLOR_SCORES)
    clarity = _grade_score(attributes.get("clarity"), _CLARITY_SCORES)
    composite = round((cut * 0.45) + (color * 0.25) + (clarity * 0.30), 1)
    pillars = {
        "cut_quality": cut,
        "color_grade": color,
        "clarity_grade": clarity,
    }
    return composite, pillars


class VanillaScorer(ScoringBackend):
    """B2B fallback when SparkleScore is not licensed."""

    def score_candidates(
        self,
        tenant_id: str,
        anchor: dict[str, Any] | None,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        scored = []
        for candidate in candidates:
            composite, pillars = vanilla_composite(candidate)
            scored.append({
                **candidate,
                "composite": composite,
                "pillars": pillars,
                "scoring_backend": "vanilla",
            })
        if anchor is not None:
            anchor_composite, anchor_pillars = vanilla_composite(anchor)
            anchor = {
                **anchor,
                "composite": anchor_composite,
                "pillars": anchor_pillars,
                "scoring_backend": "vanilla",
            }
        return scored

    def score_anchor(self, anchor: dict[str, Any]) -> dict[str, Any]:
        composite, pillars = vanilla_composite(anchor)
        return {
            **anchor,
            "composite": composite,
            "pillars": pillars,
            "scoring_backend": "vanilla",
        }
