"""FastAPI application — v1 API scaffold."""

from fastapi import FastAPI

from facet_intelligence.api.discover import router as discover_router
from facet_intelligence.api.health import router as health_router
from facet_intelligence.api.inventory import router as inventory_router
from facet_intelligence.api.recommend import router as recommend_router

app = FastAPI(
    title="Facet Intelligence",
    description="Diamond recommendation and inventory-intelligence API",
    version="0.1.0",
)

app.include_router(health_router, prefix="/v1", tags=["health"])
app.include_router(inventory_router, prefix="/v1", tags=["inventory"])
app.include_router(recommend_router, prefix="/v1", tags=["recommend"])
app.include_router(discover_router, prefix="/v1", tags=["discover"])
