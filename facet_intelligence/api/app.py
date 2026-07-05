"""FastAPI application — v1 API scaffold."""

from fastapi import FastAPI

from facet_intelligence.api.health import router as health_router

app = FastAPI(
    title="Facet Intelligence",
    description="Diamond recommendation and inventory-intelligence API",
    version="0.1.0-scaffold",
)

app.include_router(health_router, prefix="/v1", tags=["health"])
