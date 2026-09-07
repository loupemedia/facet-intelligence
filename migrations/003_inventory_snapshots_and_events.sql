-- PRD-FI-001 Epic 2: daily snapshots, miss tracking, emitted-event dedupe
-- Database: facet_intelligence

CREATE TABLE IF NOT EXISTS tenant_listing_snapshots (
    tenant_id       TEXT NOT NULL REFERENCES tenants(tenant_id),
    snapshot_date   DATE NOT NULL,
    listing_id      TEXT NOT NULL,
    stone_key       TEXT NOT NULL,
    retailer_code   TEXT NOT NULL,
    price           NUMERIC(12, 2),
    currency        TEXT,
    availability    TEXT NOT NULL DEFAULT 'in_stock',
    cert_lab        TEXT,
    cert_number     TEXT,
    product_url     TEXT,
    PRIMARY KEY (tenant_id, snapshot_date, listing_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_listing_snapshots_tenant_date
    ON tenant_listing_snapshots (tenant_id, snapshot_date);

CREATE TABLE IF NOT EXISTS tenant_listing_miss_tracking (
    tenant_id           TEXT NOT NULL REFERENCES tenants(tenant_id),
    listing_id          TEXT NOT NULL,
    first_missing_date  DATE NOT NULL,
    PRIMARY KEY (tenant_id, listing_id)
);

CREATE TABLE IF NOT EXISTS tenant_emitted_events (
    tenant_id   TEXT NOT NULL REFERENCES tenants(tenant_id),
    event_id    TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    payload     JSONB NOT NULL,
    emitted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_emitted_events_tenant_type
    ON tenant_emitted_events (tenant_id, event_type);
