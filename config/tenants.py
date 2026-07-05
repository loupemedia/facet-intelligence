"""Tenant registry — inventory source, scoring backend, mode."""

from typing import TypedDict


class TenantConfig(TypedDict):
    tenant_id: str
    scoring_backend: str
    mode: str
    inventory_source: str


# Wave 1 dogfood. Additional tenants via config — not hardcoded in business logic.
DEFAULT_TENANTS: dict[str, TenantConfig] = {
    "ringspo-us": {
        "tenant_id": "ringspo-us",
        "scoring_backend": "sparklescore",
        "mode": "cross_retailer",
        "inventory_source": "country_market:us",
    },
}


def get_tenant(tenant_id: str) -> TenantConfig:
    """Resolve tenant config or raise."""
    if tenant_id not in DEFAULT_TENANTS:
        raise KeyError(f"Unknown tenant: {tenant_id}")
    return DEFAULT_TENANTS[tenant_id]
