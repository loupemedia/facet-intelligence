"""Substitute-diamond recommendation engine."""

import logging
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Mapping, Optional

from config.tenants import get_tenant
from facet_intelligence.ingestion.models import CanonicalListing
from facet_intelligence.inventory.store import ListingStore
from facet_intelligence.recommend.anchors import resolve_anchor
from facet_intelligence.recommend.categories import MAX_ALTERNATIVES, VALID_CATEGORIES, rank_candidates
from facet_intelligence.recommend.explanations import build_alternative_payload
from facet_intelligence.recommend.models import ResolvedAnchor, ScoredCandidate
from facet_intelligence.scoring.factory import get_scoring_backend
from facet_intelligence.scoring.vanilla import VanillaScorer, vanilla_composite
from shared.pipeline_date import PIPELINE_TZ

logger = logging.getLogger(__name__)

SUBSTITUTE_DIAMOND = "substitute_diamond"


@dataclass
class RecommendResult:
    anchor: dict[str, Any]
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


def _normalize_shape(shape: Optional[str]) -> Optional[str]:
    if shape is None:
        return None
    return str(shape).strip().lower()


def _filter_candidates(
    listings: list[CanonicalListing],
    *,
    anchor: ResolvedAnchor,
    constraints: Mapping[str, Any],
) -> list[CanonicalListing]:
    budget_max = constraints.get("budget_max")
    shape = _normalize_shape(constraints.get("shape"))
    carat_tolerance = constraints.get("carat_tolerance")
    in_stock = constraints.get("in_stock", True)
    anchor_listing = anchor.listing
    anchor_carat = anchor.attributes.get("carat")
    if anchor_listing and anchor_listing.carat is not None:
        anchor_carat = anchor_listing.carat

    filtered: list[CanonicalListing] = []
    for listing in listings:
        if in_stock and listing.availability != "in_stock":
            continue
        if anchor_listing and listing.listing_id == anchor_listing.listing_id:
            continue
        if budget_max is not None and listing.price is not None and listing.price > float(budget_max):
            continue
        if shape is not None and _normalize_shape(listing.shape) != shape:
            continue
        if carat_tolerance is not None and anchor_carat is not None and listing.carat is not None:
            tolerance = float(carat_tolerance)
            if abs(listing.carat - float(anchor_carat)) > tolerance:
                continue
        filtered.append(listing)
    return filtered


def _score_with_backend(
    backend_name: str,
    tenant_id: str,
    anchor: ResolvedAnchor,
    candidates: list[CanonicalListing],
    scorer,
) -> tuple[float, list[ScoredCandidate]]:
    if backend_name == "vanilla" or isinstance(scorer, VanillaScorer):
        anchor_composite, anchor_pillars = vanilla_composite(anchor.attributes)
        anchor = replace(anchor, composite=anchor_composite)
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
        return anchor_composite, scored

    anchor_scored = scorer.score_anchor(anchor.attributes, tenant_id)
    anchor_composite = float(anchor_scored["composite"])
    anchor = replace(anchor, composite=anchor_composite)

    scored = []
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
    return anchor_composite, scored


def recommend_substitutes(
    tenant_id: str,
    body: Mapping[str, Any],
    *,
    store: Optional[ListingStore] = None,
) -> RecommendResult:
    mode = str(body.get("mode") or SUBSTITUTE_DIAMOND)
    if mode != SUBSTITUTE_DIAMOND:
        raise ValueError(f"Unsupported mode {mode!r}; v1 supports substitute_diamond only")

    category = str(body.get("category") or "good_value")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Unsupported category {category!r}")

    tenant = get_tenant(tenant_id)
    listing_store = store or ListingStore()
    anchor = resolve_anchor(tenant_id, body.get("anchor") or {}, store=listing_store)
    constraints = body.get("constraints") or {}

    backend = get_scoring_backend(
        tenant_id,
        body.get("scoring_backend"),
        tenant["scoring_backend"],
    )
    backend_name = body.get("scoring_backend") or tenant["scoring_backend"]

    if anchor.listing is None and backend_name == "sparklescore":
        raise ValueError("attributes anchor requires vanilla scoring backend in v1")

    all_listings = listing_store.fetch_listings(tenant_id, in_stock_only=bool(constraints.get("in_stock", True)))
    candidates = _filter_candidates(all_listings, anchor=anchor, constraints=constraints)

    meta: dict[str, Any] = {
        "candidate_count": len(all_listings),
        "filtered_count": len(candidates),
    }

    if not candidates:
        return RecommendResult(
            anchor=_anchor_payload(anchor),
            alternatives=[],
            generated_at=datetime.now(PIPELINE_TZ).isoformat(),
            meta={**meta, "reason_if_empty": "no_candidates_after_filters"},
        )

    anchor_composite, scored = _score_with_backend(
        backend_name,
        tenant_id,
        anchor,
        candidates,
        backend,
    )

    quality_floor = [c for c in scored if c.composite >= anchor_composite]
    meta["quality_floor_count"] = len(quality_floor)

    if not quality_floor:
        return RecommendResult(
            anchor=_anchor_payload(anchor),
            alternatives=[],
            generated_at=datetime.now(PIPELINE_TZ).isoformat(),
            meta={**meta, "reason_if_empty": "no_substitutes_meet_quality_floor"},
        )

    ranked = rank_candidates(quality_floor, category, limit=MAX_ALTERNATIVES)
    alternatives = [
        build_alternative_payload(candidate, anchor, category)
        for candidate in ranked
    ]

    return RecommendResult(
        anchor=_anchor_payload(anchor),
        alternatives=alternatives,
        generated_at=datetime.now(PIPELINE_TZ).isoformat(),
        meta=meta,
    )


def _anchor_payload(anchor: ResolvedAnchor) -> dict[str, Any]:
    payload = dict(anchor.attributes)
    if anchor.composite is not None:
        payload["composite"] = anchor.composite
    return payload
