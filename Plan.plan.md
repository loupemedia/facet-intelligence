# Facet Intelligence — Master Plan

**Status:** Scaffold (2026-07-06) — Epic 1 in progress  
**Product:** Facet Intelligence (`facet-intelligence` repo)

## Vision

Independent, licensable diamond recommendation and inventory-intelligence API. Owned sites dogfood as ordinary tenants (`ringspo-us` wave 1).

## Phases

| Phase | Scope | PRD |
|-------|-------|-----|
| **1 — Scaffold & ingestion** | Repo, CI, tenants, canonical listing schema, ingest | Epic 1 |
| **2 — Inventory signals** | Snapshot, diff, events incl. `better_match` | Epic 2 |
| **3 — Recommendations** | `/v1/recommend`, `/v1/discover`, SparkleScore client | Epic 3 |
| **4 — Dogfood** | `ringspo-us` E2E with diamond-prices client | Epic 4 |
| **5 — B2B adapters** | Klaviyo, docs (optional v1.1) | Epic 5 |

## Dependencies

1. SparkleScore SS-002 staging pilot (before Epic 3)
2. diamond-prices PRD-009 client (Epic 4)

## Cross-repo

- Vision: `../diamond-prices/docs/architecture/facet-intelligence-product-vision.md`
- Boundaries: `../diamond-prices/docs/architecture/platform-product-boundaries.md`
- Consumer surfaces: `../diamond-prices` PRD-009
