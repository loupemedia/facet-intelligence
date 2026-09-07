"""POST /v1/recommend — cert-anchored substitute diamonds."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from facet_intelligence.api.auth import require_tenant
from facet_intelligence.api.deps import get_listing_store
from facet_intelligence.inventory.store import ListingStore
from facet_intelligence.recommend.engine import recommend_substitutes

router = APIRouter()


class RecommendConstraints(BaseModel):
    budget_max: Optional[float] = None
    shape: Optional[str] = None
    carat_tolerance: Optional[float] = None
    in_stock: bool = True


class RecommendRequest(BaseModel):
    anchor: dict[str, Any]
    mode: str = Field(default="substitute_diamond")
    category: str = Field(default="good_value")
    constraints: RecommendConstraints = Field(default_factory=RecommendConstraints)
    scoring_backend: Optional[str] = None


class RecommendResponse(BaseModel):
    anchor: dict[str, Any]
    alternatives: list[dict[str, Any]]
    generated_at: str
    meta: dict[str, Any] = Field(default_factory=dict)


@router.post("/recommend", response_model=RecommendResponse)
def recommend(
    body: RecommendRequest,
    tenant_id: str = Depends(require_tenant),
    store: ListingStore = Depends(get_listing_store),
) -> RecommendResponse:
    try:
        result = recommend_substitutes(
            tenant_id,
            body.model_dump(),
            store=store,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return RecommendResponse(
        anchor=result.anchor,
        alternatives=result.alternatives,
        generated_at=result.generated_at,
        meta=result.meta,
    )
