"""Intent-first discovery — no anchor, rank filtered inventory by buyer_intent."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional

from config.tenants import get_tenant
from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.inventory.store import ListingStore
from facet_intelligence.recommend.categories import (
    MAX_ALTERNATIVES,
    VALID_CATEGORIES,
    rank_candidates,
)
from facet_intelligence.recommend.engine import _normalize_shape
from facet_intelligence.recommend.explanations import build_discover_payload
from facet_intelligence.recommend.models import ScoredCandidate
from facet_intelligence.scoring.factory import get_scoring_backend
from facet_intelligence.scoring.vanilla import VanillaScorer, vanilla_composite
from shared.pipeline_date import PIPELINE_TZ

logger = logging.getLogger(__name__)

DEFERRED_BUYER_INTENTS = frozenset({"safe_premium", "lab_value"})
VALID_BUYER_INTENTS = VALID_CATEGORIES


@dataclass
class DiscoverResult:
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


def _resolve_rank_intent(body: Mapping[str, Any]) -> str:
    buyer_intent = str(body.get("buyer_intent") or "").strip()
    if not buyer_intent:
        raise ValueError("buyer_intent is required")
    if buyer_intent in DEFERRED_BUYER_INTENTS:
        raise ValueError(f"buyer_intent {buyer_intent!r} is not supported in v1")
    if buyer_intent not in VALID_BUYER_INTENTS:
        raise ValueError(f"Unsupported buyer_intent {buyer_intent!r}")

    category = body.get("category")
    if category is not None:
        category_str = str(category).strip()
        if category_str not in VALID_CATEGORIES:
            raise ValueError(f"Unsupported category {category_str!r}")
        return category_str
    return buyer_intent


def _filter_discover_candidates(
    listings: list[CanonicalListing],
    constraints: Mapping[str, Any],
) -> list[CanonicalListing]:
    budget_max = constraints.get("budget_max")
    budget_min = constraints.get("budget_min")
    shape = _normalize_shape(constraints.get("shape"))
    carat_min = constraints.get("carat_min")
    carat_max = constraints.get("carat_max")
    diamond_type = constraints.get("diamond_type")
    in_stock = constraints.get("in_stock", True)

    filtered: list[CanonicalListing] = []
    for listing in listings:
        if in_stock and listing.availability != "in_stock":
            continue
        if budget_max is not None and listing.price is not None and listing.price > float(budget_max):
            continue
        if budget_min is not None and listing.price is not None and listing.price < float(budget_min):
            continue
        if shape is not None and _normalize_shape(listing.shape) != shape:
            continue
        if carat_min is not None and listing.carat is not None and listing.carat < float(carat_min):
            continue
        if carat_max is not None and listing.carat is not None and listing.carat > float(carat_max):
            continue
        if diamond_type is not None:
            if listing.diamond_type is None or listing.diamond_type != str(diamond_type):
                continue
        filtered.append(listing)
    return filtered


def _score_listings(
    backend_name: str,
    tenant_id: str,
    candidates: list[CanonicalListing],
    scorer,
) -> list[ScoredCandidate]:
    if backend_name == "vanilla" or isinstance(scorer, VanillaScorer):
        scored: list[ScoredCandidate] = []
        for listing in candidates:
            composite, pillars = vanilla_composite({
                "cut": listing.cut,
                "color": listing.color,
                "clarity": listing.clarity,
                "carat": listing.carat,
                "price": listing.price,
            })
            scored.append(
                ScoredCandidate(
                    listing=listing,
                    composite=composite,
                    pillars=pillars,
                    scoring_backend="vanilla",
                ),
            )
        return scored

    scored: list[ScoredCandidate] = []
    for listing in candidates:
        result = scorer.score_listing(listing, tenant_id)
        scored.append(
            ScoredCandidate(
                listing=listing,
                composite=float(result["composite"]),
                pillars=result.get("pillars") or {},
                scoring_backend="sparklescore",
            ),
        )
    return scored


def discover_listings(
    tenant_id: str,
    body: Mapping[str, Any],
    *,
    store: Optional[ListingStore] = None,
) -> DiscoverResult:
    rank_intent = _resolve_rank_intent(body)
    constraints = body.get("constraints") or {}

    tenant = get_tenant(tenant_id)
    listing_store = store or ListingStore()

    backend = get_scoring_backend(
        tenant_id,
        body.get("scoring_backend"),
        tenant["scoring_backend"],
    )
    backend_name = body.get("scoring_backend") or tenant["scoring_backend"]

    all_listings = listing_store.fetch_listings(
        tenant_id,
        in_stock_only=bool(constraints.get("in_stock", True)),
    )
    candidates = _filter_discover_candidates(all_listings, constraints)

    meta: dict[str, Any] = {
        "buyer_intent": str(body.get("buyer_intent")),
        "rank_by": rank_intent,
        "candidate_count": len(all_listings),
        "filtered_count": len(candidates),
    }

    if not candidates:
        return DiscoverResult(
            recommendations=[],
            generated_at=datetime.now(PIPELINE_TZ).isoformat(),
            meta={**meta, "reason_if_empty": "no_candidates_after_filters"},
        )

    scored = _score_listings(backend_name, tenant_id, candidates, backend)
    ranked = rank_candidates(scored, rank_intent, limit=MAX_ALTERNATIVES)
    recommendations = [
        build_discover_payload(candidate, rank_intent, rank_index=index)
        for index, candidate in enumerate(ranked)
    ]

    return DiscoverResult(
        recommendations=recommendations,
        generated_at=datetime.now(PIPELINE_TZ).isoformat(),
        meta=meta,
    )
