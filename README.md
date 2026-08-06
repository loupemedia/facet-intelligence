# Facet Intelligence

API-first, multi-tenant **diamond recommendation and inventory-intelligence** service.

## Current status (2026-08-07)

**Epic 1.1 complete** — `GET /v1/health` only. Ingestion, inventory diff, ranking, and webhooks are **planned** (Epics 1.2–5). Package stubs exist under `facet_intelligence/` but are not wired to routes.

Facet Intelligence will ingest tenant inventory, diff day-over-day, rank quality-aware recommendations (via SparkleScore), and emit webhook events (`diamond.disappeared`, `diamond.price_dropped`, `diamond.better_match`).

**Product name:** Facet Intelligence (not "Facet IQ" — avoids collision with jewellery POS "Carat IQ").

## Related repos

| Repo | Role |
|------|------|
| [`diamond-prices`](../diamond-prices) | First API client + engagement layer (PRD-009); product vision docs |
| [`sparklescoredata`](../sparklescoredata) | SparkleScore API — scoring backend for owned tenants |

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

**PRD-FI-001 and epics live in this repo** (`planning/`). Cross-repo vision: `diamond-prices/docs/architecture/facet-intelligence-product-vision.md` and `platform-product-boundaries.md`.

## Deployment

Sevalla (Docker + gunicorn/uvicorn). Canonical timezone: **Australia/Brisbane** — use `shared.pipeline_date.pipeline_today()`.

## See also

- [`Plan.plan.md`](Plan.plan.md) — phase roadmap
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system design
- [`docs/SYSTEM_DEPENDENCIES.md`](docs/SYSTEM_DEPENDENCIES.md) — integration map
