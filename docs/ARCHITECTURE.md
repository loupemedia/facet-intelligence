# Facet Intelligence Architecture

## Strategic positioning

Facet Intelligence is the **quality-aware recommendation and inventory-intelligence API** between SparkleScore (scoring) and engagement/ESPs (delivery).

| Question | Owner |
|----------|-------|
| How good is this stone? | **SparkleScore** |
| Which stone should I show / what changed in inventory? | **Facet Intelligence** |
| Who gets an email? | **diamond-prices** engagement (CP 49) or retailer ESP |

**Facet Intelligence calls SparkleScore; SparkleScore never calls Facet Intelligence.**

## Cross-repo docs

| Topic | Location |
|-------|----------|
| Product vision | `diamond-prices/docs/architecture/facet-intelligence-product-vision.md` |
| Platform map | `diamond-prices/docs/architecture/platform-product-boundaries.md` |
| Consumer surfaces | `diamond-prices` PRD-009 |
| SparkleScore scope | `sparklescoredata/docs/ARCHITECTURE.md` |
| Continuous carat scoring (parked) | `sparklescoredata/docs/continuous-carat-scoring.md` — fixes off-band Value/Face-Up (e.g. 1.26 ct); **not implemented** |
| Upstream feed obligations | `diamond-prices/docs/architecture/sparklescore-continuous-scoring.md` |

## Data flow

### Current implementation (2026-07-06 scaffold)

| Component | Status |
|-----------|--------|
| `GET /v1/health` | ✅ Live |
| `ingestion/`, `inventory/`, `recommend/`, `events/` | Package stubs only |
| `SparkleScoreClient` | Interface + `NotImplementedError` stub |
| `DatabasePool` | Helper exists; not wired to API |

### Target architecture

```text
Tenant inventory (CSV/JSON/feed/country pool)
        │
        ▼
  ingestion/ → normalize → listing_id
        │
        ▼
  inventory/snapshot (daily per tenant)
        │
        ├── diff → events (disappeared, price_dropped, better_match)
        │
        └── recommend/discover → filter → SparkleScore (top N) → rank
                    │
                    ▼
              webhook → diamond-prices engagement / B2B ESP
```

## Multi-tenant model

Every row, query, and event carries `tenant_id`. Wave-1 dogfood: `ringspo-us` (`scoring_backend: sparklescore`).

Owned tenants **must** use SparkleScore — vanilla is B2B-only.

## API (v1)

See `docs/architecture/facet-intelligence-bootstrap-prompt.md` in `diamond-prices` for full contract. Implemented routes start with `GET /v1/health`.

## Deployment

Sevalla — Docker, FastAPI, gunicorn + uvicorn workers. Database: `facet_intelligence` (separate from `diamond-prices` and `sparklescore`).
