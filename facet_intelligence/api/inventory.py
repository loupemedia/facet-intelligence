"""POST /v1/inventory/sync — tenant inventory ingest."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from facet_intelligence.api.auth import require_tenant
from facet_intelligence.api.deps import get_listing_store
from facet_intelligence.inventory.store import ListingStore
from facet_intelligence.inventory.sync import sync_tenant_inventory

router = APIRouter()


class InventorySyncRequest(BaseModel):
    source: str = Field(default="json", description="csv, json, export, feed, or db")
    listings: list[dict[str, Any]]


class InventorySyncResponse(BaseModel):
    status: str
    tenant_id: str
    listing_count: int
    rows_upserted: int
    event_id: str
    synced_at: str


@router.post(
    "/inventory/sync",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=InventorySyncResponse,
)
def inventory_sync(
    body: InventorySyncRequest,
    tenant_id: str = Depends(require_tenant),
    store: ListingStore = Depends(get_listing_store),
) -> InventorySyncResponse:
    try:
        result = sync_tenant_inventory(
            tenant_id,
            body.model_dump(),
            store=store,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return InventorySyncResponse(
        status="accepted",
        tenant_id=result.tenant_id,
        listing_count=result.listing_count,
        rows_upserted=result.rows_upserted,
        event_id=result.event_id,
        synced_at=result.synced_at.isoformat(),
    )
