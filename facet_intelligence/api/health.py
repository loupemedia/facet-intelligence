"""Health check route."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "facet-intelligence",
        "version": "0.1.0-scaffold",
    }
