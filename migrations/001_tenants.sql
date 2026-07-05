-- PRD-FI-001 Epic 1: tenant registry (scaffold)
-- Database: facet_intelligence

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id       TEXT PRIMARY KEY,
    scoring_backend TEXT NOT NULL DEFAULT 'sparklescore',
    mode            TEXT NOT NULL DEFAULT 'cross_retailer',
    inventory_source TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO tenants (tenant_id, scoring_backend, mode, inventory_source)
VALUES ('ringspo-us', 'sparklescore', 'cross_retailer', 'country_market:us')
ON CONFLICT (tenant_id) DO NOTHING;
