# Facet Intelligence

API-first, multi-tenant **diamond recommendation and inventory-intelligence** service.

## Current status (2026-08-07)

**Epic 3 complete** — `POST /v1/recommend` and `POST /v1/discover` live (quality floor on recommend, intent-first discover).

Facet Intelligence will ingest tenant inventory, diff day-over-day, rank quality-aware recommendations (via SparkleScore), and emit webhook events (`diamond.disappeared`, `diamond.price_dropped`, `diamond.better_match`).

**Product name:** Facet Intelligence (not "Facet IQ" — avoids collision with jewellery POS "Carat IQ").

## Related repos

| Repo | Role |
|------|------|
| [`diamond-prices`](../diamond-prices) | First API client + engagement layer (PRD-009); product vision docs |
| [`sparklescoredata`](../sparklescoredata) | SparkleScore API — scoring backend for owned tenants |

**Epic 2 in progress** — daily snapshots, disappearance (2-day grace), price-drop events, webhook delivery. Run `python scripts/F1_daily_inventory_signals.py` after sync. Apply migration `003` in TablePlus before first run.

## Daily signals

```bash
python scripts/F1_daily_inventory_signals.py --tenant ringspo-us
python scripts/F1_daily_inventory_signals.py --date 2026-03-07 --dry-run
```

Set `RINGSPO_US_WEBHOOK_URL` for webhook delivery to the engagement layer.

## API (staging)

```bash
curl -X POST http://localhost:8000/v1/inventory/sync \
  -H "Authorization: Bearer $FACET_INTELLIGENCE_API_KEY" \
  -H "X-Facet-Intelligence-Tenant: ringspo-us" \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/feed_us_json.json
```

Returns **202** with `listing_count`, `event_id`, and `synced_at`. Out-of-pool retailers are filtered for `ringspo-us`.

**Database:** apply migrations `002` and `003` in TablePlus before first sync/signals run (see `migrations/README.md`).

### Recommend

```bash
curl -X POST http://localhost:8000/v1/recommend \
  -H "Authorization: Bearer $FACET_INTELLIGENCE_API_KEY" \
  -H "X-Facet-Intelligence-Tenant: ringspo-us" \
  -H "Content-Type: application/json" \
  -d '{
    "anchor": {"listing_id": "BN_2527938255"},
    "mode": "substitute_diamond",
    "category": "good_value",
    "constraints": {"budget_max": 8000, "in_stock": true}
  }'
```

Requires `SPARKLESCORE_API_URL` and `SPARKLESCORE_API_KEY` for `ringspo-us`. Returns up to 5 alternatives with `score`, `headline`, and `reason_codes[]`.

### Discover

```bash
curl -X POST http://localhost:8000/v1/discover \
  -H "Authorization: Bearer $FACET_INTELLIGENCE_API_KEY" \
  -H "X-Facet-Intelligence-Tenant: ringspo-us" \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_intent": "best_sparkle",
    "constraints": {"budget_max": 8000, "shape": "round", "in_stock": true}
  }'
```

Returns up to 5 `recommendations[]` (same item shape as recommend alternatives). Optional `category` overrides ranking while `buyer_intent` records consumer intent. `safe_premium` and `lab_value` are deferred in v1.

## Quick start

```bash
git clone <repo-url>
cd facet-intelligence

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

pytest tests/unit/ -v
ruff check .
```

## Environment variables

See [`docs/SECURITY_HARDENING.md`](docs/SECURITY_HARDENING.md). Minimum for local dev:

| Variable | Purpose |
|----------|---------|
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | PostgreSQL (`facet_intelligence` database) |
| `FACET_INTELLIGENCE_API_KEY` | Tenant API auth (dev) |
| `SPARKLESCORE_API_URL`, `SPARKLESCORE_API_KEY` | SparkleScore client (Epic 3+) |

## Project structure (target layout — stubs today)

```
facet_intelligence/   # Core package
├── ingestion/        # Feed → canonical listing schema
├── inventory/        # Snapshots, diff, signals
├── scoring/          # SparkleScore + vanilla backends
├── recommend/        # Quality floor, categories, rank
├── events/           # Webhook / ESP adapters
└── api/              # FastAPI v1 routes

shared/               # db, pipeline_date, services/
scripts/              # F-series batch entrypoints (F{N}_*.py) — when added
planning/             # PRD-FI-001, epics, stories (canonical planning home)
migrations/           # facet_intelligence PostgreSQL
```

## Planning home

**PRD-FI-001 and epics live in this repo** (`planning/`). Cross-repo vision: `diamond-prices/docs/architecture/facet-intelligence-product-vision.md` and `platform-product-boundaries.md`. Studio UI + later agent citation (not a PRD): `diamond-prices/docs/strategy/diamond-decision-experience.md`.

## Deployment

Sevalla (Docker + gunicorn/uvicorn). Canonical timezone: **Australia/Brisbane** — use `shared.pipeline_date.pipeline_today()`.

## See also

- [`Plan.plan.md`](Plan.plan.md) — phase roadmap
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system design
- [`docs/SYSTEM_DEPENDENCIES.md`](docs/SYSTEM_DEPENDENCIES.md) — integration map
