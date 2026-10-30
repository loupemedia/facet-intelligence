# Facet Intelligence — Master Plan

**Status:** Epic 3 complete — `POST /v1/recommend` and `POST /v1/discover` shipped  
**Updated:** 2026-09-10  
**Product:** Facet Intelligence (`facet-intelligence` repo)

## Vision

Independent, licensable diamond recommendation and inventory-intelligence API. Owned sites dogfood as ordinary tenants (`ringspo-us` wave 1).

## Current state

| Item | Status |
|------|--------|
| Repo scaffold (CI, FastAPI health, package layout, migrations shell) | ✅ Story 1.1 |
| Canonical listing normalisation + `listing_id` | ✅ Story 1.2 |
| Feed loader + `ringspo-us` country-pool adapter | ✅ Story 1.3 |
| `POST /v1/inventory/sync` + `inventory.synced` stub | ✅ Story 1.4 |
| `POST /v1/recommend` (substitute_diamond, quality floor) | ✅ Epic 3.3 |
| `POST /v1/discover` (intent-first) | ✅ Epic 3.4 |
| Webhook outbox (deliver before dedupe; snapshot always) | ✅ Epic 2 Story 2.5 (2026-09-10) |

**Cross-repo dogfood sequence (P0–P3):** [`diamond-prices/docs/operations/facet-intelligence-staging-e2e.md`](../diamond-prices/docs/operations/facet-intelligence-staging-e2e.md) § Dogfood closure sequence.

## Phases

| Phase | Scope | PRD |
|-------|-------|-----|
| **1 — Scaffold & ingestion** | Repo, CI, tenants, canonical listing schema, ingest | Epic 1 (1.1 ✅) |
| **2 — Inventory signals** | Snapshot, diff, events incl. `better_match` | Epic 2 |
| **3 — Recommendations** | `/v1/recommend`, `/v1/discover`, SparkleScore client | Epic 3 |
| **4 — Dogfood** | `ringspo-us` E2E with diamond-prices client | Epic 4 |
| **5 — B2B adapters** | Klaviyo, docs (optional v1.1) | Epic 5 |

## Dependencies

1. SparkleScore SS-002 API **implemented**; staging pilot sign-off pending (before Epic 3 wiring) — see [`sparklescoredata/Plan.plan.md`](../sparklescoredata/Plan.plan.md)
2. diamond-prices PRD-009 client (Epic 4)

## Planning & cross-repo

- PRD index: [`planning/PRD_INDEX.md`](planning/PRD_INDEX.md)
- PRD-FI-001: [`planning/PRDs/PRD-FI-001_facet-intelligence-recommendation-and-inventory-intelligence.md`](planning/PRDs/PRD-FI-001_facet-intelligence-recommendation-and-inventory-intelligence.md)
- Vision: [`../diamond-prices/docs/architecture/facet-intelligence-product-vision.md`](../diamond-prices/docs/architecture/facet-intelligence-product-vision.md)
- Boundaries: [`../diamond-prices/docs/architecture/platform-product-boundaries.md`](../diamond-prices/docs/architecture/platform-product-boundaries.md)
- Consumer surfaces: `../diamond-prices` PRD-009
- Decision studio + later agent citation (not a PRD): [`../diamond-prices/docs/strategy/diamond-decision-experience.md`](../diamond-prices/docs/strategy/diamond-decision-experience.md)
- GTM (canonical): [`../diamond-prices/docs/strategy/gtm/README.md`](../diamond-prices/docs/strategy/gtm/README.md)
