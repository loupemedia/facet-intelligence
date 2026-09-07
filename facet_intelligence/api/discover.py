"""POST /v1/discover — intent-first shortlists (no anchor)."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from facet_intelligence.api.auth import require_tenant
from facet_intelligence.api.deps import get_listing_store
from facet_intelligence.inventory.store import ListingStore
from facet_intelligence.recommend.discover import discover_listings

router = APIRouter()


class DiscoverConstraints(BaseModel):
    budget_max: Optional[float] = None
    budget_min: Optional[float] = None
    shape: Optional[str] = None
    carat_min: Optional[float] = None
    carat_max: Optional[float] = None
    diamond_type: Optional[str] = None
    country_code: Optional[str] = None
    in_stock: bool = True


class DiscoverRequest(BaseModel):
    buyer_intent: str
    category: Optional[str] = None
    constraints: DiscoverConstraints = Field(default_factory=DiscoverConstraints)
    scoring_backend: Optional[str] = None


class DiscoverResponse(BaseModel):
    recommendations: list[dict[str, Any]]
    generated_at: str
    meta: dict[str, Any] = Field(default_factory=dict)


@router.post("/discover", response_model=DiscoverResponse)
def discover(
    body: DiscoverRequest,
    tenant_id: str = Depends(require_tenant),
    store: ListingStore = Depends(get_listing_store),
) -> DiscoverResponse:
    try:
        result = discover_listings(
            tenant_id,
            body.model_dump(),
            store=store,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return DiscoverResponse(
        recommendations=result.recommendations,
        generated_at=result.generated_at,
        meta=result.meta,
    )
