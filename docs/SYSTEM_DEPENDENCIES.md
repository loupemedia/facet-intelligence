# System Dependencies

## Upstream (Facet Intelligence reads / calls)

| System | What | Purpose |
|--------|------|---------|
| **SparkleScore API** | `POST /api/v1/score` | Per-candidate quality for recommend/discover — **SS-002 API implemented**; staging pilot sign-off pending before Epic 3 wiring |
| **SparkleScore PRD-SS-005** (parked) | `sparklescoredata/docs/continuous-carat-scoring.md` | **Known gap:** MVP Value/Face-Up fail for off-band carats (e.g. 1.26 ct) until continuous scoring ships |
| **diamond-prices R1 feeds** | Country retailer pools | `ringspo-us` inventory source (dogfood) |
| **`country_markets.yaml`** | Tenant → retailer mapping | Config in diamond-prices |

## Downstream (calls Facet Intelligence)

| System | What |
|--------|------|
| **diamond-prices** | HTTP client (`discover`, `recommend`); webhook receiver for CP 49 |
| **B2B retailers** | Same public API + webhooks |
| **Klaviyo / ESP** | Optional event adapters (Epic 5) |

## Product vision (cross-repo)

`diamond-prices/docs/architecture/facet-intelligence-product-vision.md`

Decision studio UI + later agent citation (not a PRD): `diamond-prices/docs/strategy/diamond-decision-experience.md`
