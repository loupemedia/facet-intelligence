"""Scoring backend selection — sparklescore (owned) | vanilla (B2B)."""

SPARKLESCORE = "sparklescore"
VANILLA = "vanilla"

OWNED_TENANT_BACKENDS = {SPARKLESCORE}


def resolve_backend(tenant_id: str, requested: str | None, tenant_default: str) -> str:
    """Return scoring backend; owned tenants may only use sparklescore."""
    backend = requested or tenant_default
    if tenant_id.startswith("ringspo-") and backend != SPARKLESCORE:
        raise ValueError(f"Owned tenant {tenant_id} requires sparklescore backend")
    return backend
