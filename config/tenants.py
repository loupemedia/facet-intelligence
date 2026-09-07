"""Tenant registry — inventory source, scoring backend, mode, signal config."""

import os
from typing import TypedDict


class TenantConfig(TypedDict):
    tenant_id: str
    scoring_backend: str
    mode: str
    inventory_source: str
    grace_period_days: int
    price_drop_min_pct: float
    webhook_env_var: str


# Wave 1 dogfood. Additional tenants via config — not hardcoded in business logic.
DEFAULT_TENANTS: dict[str, TenantConfig] = {
    "ringspo-us": {
        "tenant_id": "ringspo-us",
        "scoring_backend": "sparklescore",
        "mode": "cross_retailer",
        "inventory_source": "country_market:us",
        "grace_period_days": 2,
        "price_drop_min_pct": 1.0,
        "webhook_env_var": "RINGSPO_US_WEBHOOK_URL",
    },
}


def get_tenant(tenant_id: str) -> TenantConfig:
    """Resolve tenant config or raise."""
    if tenant_id not in DEFAULT_TENANTS:
        raise KeyError(f"Unknown tenant: {tenant_id}")
    return DEFAULT_TENANTS[tenant_id]


def tenant_webhook_url(tenant_id: str) -> str | None:
    """Resolve webhook URL from tenant env var, or None when unset."""
    tenant = get_tenant(tenant_id)
    env_var = tenant.get("webhook_env_var")
    if not env_var:
        return None
    return os.environ.get(env_var) or None
