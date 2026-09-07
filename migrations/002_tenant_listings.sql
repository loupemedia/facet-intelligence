-- PRD-FI-001 Story 1.4: tenant inventory listings (canonical schema)
-- Database: facet_intelligence

CREATE TABLE IF NOT EXISTS tenant_listings (
    tenant_id           TEXT NOT NULL REFERENCES tenants(tenant_id),
    listing_id          TEXT NOT NULL,
    stone_key           TEXT NOT NULL,
    retailer_code       TEXT NOT NULL,
    item_type           TEXT NOT NULL DEFAULT 'diamond',
    cert_lab            TEXT,
    cert_number         TEXT,
    retailer_diamond_id TEXT,
    diamond_type        TEXT,
    shape               TEXT,
    carat               NUMERIC(8, 2),
    color               TEXT,
    clarity             TEXT,
    cut                 TEXT,
    length_mm           NUMERIC(8, 3),
    width_mm            NUMERIC(8, 3),
    depth_mm            NUMERIC(8, 3),
    price               NUMERIC(12, 2),
    currency            TEXT,
    availability        TEXT NOT NULL DEFAULT 'in_stock',
    product_url         TEXT,
    image_url           TEXT,
    first_synced_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_synced_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, listing_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_listings_tenant_stone_key
    ON tenant_listings (tenant_id, stone_key);

CREATE INDEX IF NOT EXISTS idx_tenant_listings_tenant_retailer
    ON tenant_listings (tenant_id, retailer_code);
