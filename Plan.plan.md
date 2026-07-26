# Facet Intelligence — Master Plan

**Status:** Scaffold complete (2026-07-06); Epic 1.1 done — **next: Epic 1.2–1.4 ingestion**  
**Updated:** 2026-07-26  
**Product:** Facet Intelligence (`facet-intelligence` repo)

## Vision

Independent, licensable diamond recommendation and inventory-intelligence API. Owned sites dogfood as ordinary tenants (`ringspo-us` wave 1).

## Current state

| Item | Status |
|------|--------|
| Repo scaffold (CI, FastAPI health, package layout, migrations shell) | ✅ Story 1.1 |
| Canonical listing normalisation + `listing_id` | 📋 Story 1.2 |
| Feed loader + `ringspo-us` country-pool adapter | 📋 Story 1.3 |
| `POST /v1/inventory/sync` + `inventory.synced` stub | 📋 Story 1.4 |
| Inventory signals / recommend / dogfood | Later epics |

## Phases

| Phase | Scope | PRD |
|-------|-------|-----|
| **1 — Scaffold & ingestion** | Repo, CI, tenants, canonical listing schema, ingest | Epic 1 (1.1 ✅) |
| **2 — Inventory signals** | Snapshot, diff, events incl. `better_match` | Epic 2 |
| **3 — Recommendations** | `/v1/recommend`, `/v1/discover`, SparkleScore client | Epic 3 |
| **4 — Dogfood** | `ringspo-us` E2E with diamond-prices client | Epic 4 |
| **5 — B2B adapters** | Klaviyo, docs (optional v1.1) | Epic 5 |

## Dependencies

1. SparkleScore SS-002 staging pilot (before Epic 3) — see [`sparklescoredata/Plan.plan.md`](../sparklescoredata/Plan.plan.md)
2. diamond-prices PRD-009 client (Epic 4)

## Planning & cross-repo

- PRD index: [`planning/PRD_INDEX.md`](planning/PRD_INDEX.md)
- PRD-FI-001: [`planning/PRDs/PRD-FI-001_facet-intelligence-recommendation-and-inventory-intelligence.md`](planning/PRDs/PRD-FI-001_facet-intelligence-recommendation-and-inventory-intelligence.md)
- Vision: [`../diamond-prices/docs/architecture/facet-intelligence-product-vision.md`](../diamond-prices/docs/architecture/facet-intelligence-product-vision.md)
- Boundaries: [`../diamond-prices/docs/architecture/platform-product-boundaries.md`](../diamond-prices/docs/architecture/platform-product-boundaries.md)
- Consumer surfaces: `../diamond-prices` PRD-009
- GTM (canonical): [`../diamond-prices/docs/strategy/gtm/README.md`](../diamond-prices/docs/strategy/gtm/README.md)
