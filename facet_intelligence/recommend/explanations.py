"""Deterministic reason_codes and headlines (not LLM-generated)."""

from facet_intelligence.recommend.categories import (
    BEST_SPARKLE,
    GOOD_VALUE,
    LOOK_LARGEST,
)
from facet_intelligence.recommend.models import ResolvedAnchor, ScoredCandidate

__all__ = [
    "build_alternative_payload",
]


def _reason_codes(
    candidate: ScoredCandidate,
    anchor: ResolvedAnchor,
    category: str,
) -> list[str]:
    codes = ["meets_quality_floor"]
    anchor_composite = anchor.composite or 0.0
    if candidate.composite > anchor_composite:
        codes.append("higher_composite_than_anchor")
    if category == GOOD_VALUE and anchor.listing and candidate.listing.price and anchor.listing.price:
        if candidate.listing.price < anchor.listing.price:
            codes.append("lower_price")
    if category == LOOK_LARGEST and anchor.listing and candidate.listing.carat and anchor.listing.carat:
        if candidate.listing.carat > anchor.listing.carat:
            codes.append("larger_carat")
    if category == BEST_SPARKLE and candidate.composite >= anchor_composite:
        codes.append("best_sparkle_in_pool")
    return codes


def _headline(candidate: ScoredCandidate, anchor: ResolvedAnchor, category: str) -> str:
    score_text = f"{candidate.composite:.0f}"
    if category == GOOD_VALUE and candidate.listing.price is not None:
        return f"Scores {score_text} at ${candidate.listing.price:,.0f}"
    if category == LOOK_LARGEST and candidate.listing.carat is not None:
        return f"Scores {score_text} at {candidate.listing.carat:.2f} ct"
    if category == BEST_SPARKLE:
        return f"Top sparkle score {score_text} in your search"
    return f"Scores {score_text}"


def build_discover_payload(
    candidate: ScoredCandidate,
    buyer_intent: str,
    *,
    rank_index: int = 0,
) -> dict:
    listing = candidate.listing
    return {
        "listing_id": listing.listing_id,
        "stone_key": listing.stone_key,
        "retailer_code": listing.retailer_code,
        "price": listing.price,
        "currency": listing.currency,
        "score": {
            "composite": candidate.composite,
            "pillars": candidate.pillars,
            "backend": candidate.scoring_backend,
        },
        "product_url": listing.product_url,
        "image_url": listing.image_url,
        "cert_lab": listing.cert_lab,
        "cert_number": listing.cert_number,
        "shape": listing.shape,
        "carat": listing.carat,
        "diamond_type": listing.diamond_type,
        "headline": _discover_headline(candidate, buyer_intent),
        "reason_codes": _discover_reason_codes(candidate, buyer_intent, rank_index),
    }


def _discover_reason_codes(
    candidate: ScoredCandidate,
    buyer_intent: str,
    rank_index: int,
) -> list[str]:
    codes = ["matches_intent"]
    if buyer_intent == GOOD_VALUE:
        codes.append("value_ranked")
    elif buyer_intent == LOOK_LARGEST:
        codes.append("size_ranked")
    elif buyer_intent == BEST_SPARKLE:
        codes.append("sparkle_ranked")
    if rank_index == 0:
        codes.append("top_ranked")
    return codes


def _discover_headline(candidate: ScoredCandidate, buyer_intent: str) -> str:
    score_text = f"{candidate.composite:.0f}"
    if buyer_intent == GOOD_VALUE and candidate.listing.price is not None:
        return f"Scores {score_text} at ${candidate.listing.price:,.0f}"
    if buyer_intent == LOOK_LARGEST and candidate.listing.carat is not None:
        return f"Scores {score_text} at {candidate.listing.carat:.2f} ct"
    if buyer_intent == BEST_SPARKLE:
        return f"Top sparkle score {score_text} in your search"
    return f"Scores {score_text}"


def build_alternative_payload(
    candidate: ScoredCandidate,
    anchor: ResolvedAnchor,
    category: str,
) -> dict:
    listing = candidate.listing
    return {
        "listing_id": listing.listing_id,
        "stone_key": listing.stone_key,
        "retailer_code": listing.retailer_code,
        "price": listing.price,
        "currency": listing.currency,
        "score": {
            "composite": candidate.composite,
            "pillars": candidate.pillars,
            "backend": candidate.scoring_backend,
        },
        "product_url": listing.product_url,
        "image_url": listing.image_url,
        "cert_lab": listing.cert_lab,
        "cert_number": listing.cert_number,
        "shape": listing.shape,
        "carat": listing.carat,
        "headline": _headline(candidate, anchor, category),
        "reason_codes": _reason_codes(candidate, anchor, category),
    }
