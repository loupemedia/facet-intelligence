"""API authentication and tenant scoping."""

import os
import secrets

from fastapi import Header, HTTPException, status

from config.tenants import get_tenant

TENANT_HEADER = "X-Facet-Intelligence-Tenant"


def verify_bearer_token(authorization: str | None) -> None:
    expected = os.environ.get("FACET_INTELLIGENCE_API_KEY")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured",
        )
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


def require_tenant(
    authorization: str | None = Header(default=None, alias="Authorization"),
    tenant_id: str | None = Header(default=None, alias=TENANT_HEADER),
) -> str:
    verify_bearer_token(authorization)
    if not tenant_id or not tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing {TENANT_HEADER} header",
        )
    normalized = tenant_id.strip()
    try:
        get_tenant(normalized)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown tenant: {normalized}",
        ) from exc
    return normalized
