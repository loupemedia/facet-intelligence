---
prd_number: PRD-FI-001
title: "Facet Intelligence — Recommendation & Inventory Intelligence API"
status: draft
phase: "Pre-build planning — implements CP 48 engine; future `facet-intelligence` repo"
created: 2026-07-05
owner: Alastair Smith
related_checkpoints: [CP 48]
related_prds: [PRD-009, PRD-SS-002, PRD-SS-003]
repo: facet-intelligence
scaffolded: 2026-07-06
---

# PRD-FI-001: Facet Intelligence — Recommendation & Inventory Intelligence API

> **Planning home:** This PRD and epics live in **`facet-intelligence/planning/`** (canonical). Cross-repo vision and platform map stay in `diamond-prices/docs/architecture/`. Code: `facet_intelligence/` package in this repo.

## 1. Problem statement

SparkleScore answers **how good is this stone?** — but owned sites and B2B retailers also need **which stone to buy**, **why**, and **what changed in inventory** (sold, price drop, better match). Today:

- **PRD-SS-003** will deliver cert-anchored alternatives from a **scored corpus** — necessary but not sufficient for intent-first discovery or live inventory monitoring.
- **Phase 8 CP 48** was scoped as a recommendation engine inside `diamond-prices`; **planning decision (2026-07-05)** moves that engine to a separate **Facet Intelligence** product/repo for independence, B2B licensing, and clean seams with SparkleScore.
- **CP 49** (email) needs disappearance/price-drop signals and quality-matched alternatives — without duplicating feed-diff logic in the engagement layer.

Facet Intelligence is the **deterministic decision engine**: ingest tenant inventory, diff day-over-day, rank candidates with a quality floor, emit webhook events. Conversational UI, gated score display, and email dispatch stay in `diamond-prices` (see [`facet-intelligence-product-vision.md`](../../../../diamond-prices/docs/architecture/facet-intelligence-product-vision.md)).

## 2. User value

**Owned consumer sites (Ringspo wave-1 tenant `ringspo-us`).** Intent-first shortlists (`POST /v1/discover`), cert-anchored substitutes (`POST /v1/recommend`), and inventory events that power sold/price-drop emails — without building recommendation logic in the WP plugin.

**B2B retailers (future).** Licensable API: quality-aware recommendations + inventory intelligence events into their ESP (Klaviyo/webhook). Pluggable scoring: SparkleScore or vanilla.

**End consumers (indirect).** Multi-modal buying (filters, optional bot, cert-in) with explainable shortlists and market monitoring — powered by data, not sales pressure.

**Internal team.** One service dogfoods on owned sites through the **same public API** third parties use; no internal-only code path.

## 3. Scope

### In scope (v1 — dogfood on owned country pools)

- **Repository scaffold** — per [`facet-intelligence-bootstrap-prompt.md`](../../../../diamond-prices/docs/architecture/facet-intelligence-bootstrap-prompt.md): multi-tenant from day one, engineering principles, CI, `facet_intelligence` PostgreSQL DB. **Scaffolded 2026-07-06** (`GET /v1/health` live).
- **Canonical listing schema** — `listing_id`, `item_type`, cert, 4Cs, mm, price, retailer, availability; diamond-only implemented.
- **Inventory ingest** — CSV/JSON/feed + adapter for country retailer pools (`country_markets.yaml` retailers as first tenants).
- **Snapshot + diff** — per-tenant daily snapshot; disappearance (set-difference + 2–3 day grace); price-drop vs tenant price history.
- **Event emission** — idempotent `diamond.disappeared`, `diamond.price_dropped`, `diamond.better_match`, `inventory.synced`; webhook adapter (+ optional Klaviyo-shaped payload).
- **Recommend engine** — filter → quality floor → category rank → `reason_codes[]` + headline:
  - Categories: `good_value`, `look_largest`, `best_sparkle` (v1); `safe_premium`, `lab_value` (documented enum, may follow in v1.1).
- **API** — `POST /v1/inventory/sync`, `POST /v1/recommend` (anchor: `listing_id` | `cert` | `attributes`), `POST /v1/discover` (intent-first), `GET /v1/health`.
- **Scoring backends** — SparkleScore client (**required** for owned tenants `ringspo-us` wave 1); vanilla scorer for B2B tenants without SparkleScore licence only.
- **Dogfood tenants** — `ringspo-us` (wave 1); additional owned tenants via config (`diamondhunt-uk`, etc.) — same API surface as B2B.

### Out of scope (v1)

- **Email send / consent / templates** — engagement layer in `diamond-prices` (CP 49); Facet Intelligence emits events only.
- **Conversational UI / LLM** — consumer layer parses intent → calls `/v1/discover`; bot narrates `reason_codes` only.
- **Gated SparkleScore display** — consumer plugin gates presentation; SparkleScore returns full pillars.
- **Stone input UX** — Diamond Check tabs (cert, URL, manual, PDF upload) are **PRD-009** / CP 53; see [`stone-input-paths.md`](../../../../diamond-prices/docs/architecture/stone-input-paths.md). Facet Intelligence accepts resolved anchors only.
- **URL resolution & report parsing** — SparkleScore PRD-SS-004 (future); consumer layer may pre-resolve to `listing_id` or `cert` before Facet Intelligence calls.
- **Ring builder / setting modes** — `pair_setting` / `pair_stone` deferred (schema carries `mode` for later).
- **Monetisation / billing** — design for metering; implement in later phase.
- **Scoring methodology** — SparkleScore owns quality standard; Facet Intelligence calls API.
- **SS-003 corpus recommendations** — remains in SparkleScore for cert-widget flows; Facet Intelligence may call SparkleScore per candidate but does not replace `POST /api/v1/recommendations`.

### Owned-site integration (diamond-prices — not Facet Intelligence repo)

Documented in **PRD-009** (CP 46–47, 49–50): accounts, shortlists, plugin surfaces, email capture, SES dispatch, analytics. CP 48 **integrates** Facet Intelligence API + consumes events.

## 4. Dependencies

| Dependency | Purpose |
|------------|---------|
| **SparkleScore API** (SS-002 live, SS-003 helpful) | Per-stone scoring for recommend rank |
| **PRD-SS-003** (optional overlap) | Cert-anchored corpus query for widget; Facet Intelligence for live inventory |
| **R1 / `listing_id`** (CP 12) | Stable per-stone keys for diff + shortlists |
| **`country_markets.yaml`** | Tenant inventory sources for dogfood |
| **CP 97** (SES) | Not Facet Intelligence — engagement layer |
| **PRD-009** | Consumer surfaces that call Facet Intelligence |

**Build sequence:** SparkleScore API live → Facet Intelligence v1 → `diamond-prices` engagement (CP 49) consumes events → Phase 8 plugin integration (CP 48 client).

## 5. Success criteria

- `ringspo-us` tenant ingests US country pool; daily diff detects disappearance with grace period; webhook/event emitted with idempotent `event_id`.
- `POST /v1/discover` with `buyer_intent: best_sparkle`, budget $8k, round → returns ≤5 alternatives with SparkleScore composite, `reason_codes`, and product metadata for affiliate linking.
- `POST /v1/recommend` with anchor cert → returns only **equally good or better** substitutes (quality floor); empty set returns `200` with clear `meta.reason_if_empty`.
- Price-drop event fires when listing price decreases ≥ configured threshold vs tenant history.
- **Better-match event** fires when a new or updated listing strictly beats a watched anchor on SparkleScore quality floor (composite ≥ anchor) within subscriber budget/intent constraints.
- Dogfood integration: `diamond-prices` staging consumer layer receives `diamond.disappeared` and fetches alternatives via recommend API for CP 49 email body (end-to-end staging test).
- Multi-tenant isolation: tenant A cannot read tenant B inventory or events (automated test).
- CI: unit tests for diff, recommend rank, event idempotency; no secrets in git.

## 6. Discovery objectives / open questions

1. **Ingest frequency** — daily batch aligned with R1, or on-demand `inventory/sync` from pool export? (Recommend: daily cron per tenant + manual sync for staging.)
2. **Grace period** — 2 vs 3 days for disappearance? (Recommend: 2 days default, tenant-configurable.)
3. **Discover candidate pool** — full in-stock tenant inventory vs pre-filtered band? (Recommend: SQL pre-filter on constraints, then score top N via SparkleScore batch.)
4. **Vanilla scorer** — B2B-only when tenant does not license SparkleScore; owned dogfood tenants use `sparklescore` only.
5. **Event transport to CP 49** — webhook to internal engagement endpoint vs shared queue? (Recommend: webhook to `diamond-prices` engagement service boundary; queue if volume requires.)
6. **`buyer_intent` vs `category`** — single field or both? (Recommend: `buyer_intent` on discover; `category` alias for recommend; document in `INTENT_SCHEMA.md` at scaffold.)

## 7. Epics

| Epic | Title | Phase | Checkpoint |
|------|-------|-------|------------|
| [Epic 1](../epics/PRD-FI-001/epic-1_scaffold-and-ingestion.md) | Scaffold, tenancy & ingestion | 1 | CP 48 (foundation) |
| [Epic 2](../epics/PRD-FI-001/epic-2_inventory-signals.md) | Inventory snapshot, diff & events | 2 | CP 48 + CP 49 (signals) |
| [Epic 3](../epics/PRD-FI-001/epic-3_recommendation-engine.md) | Recommend + discover API | 3 | CP 48 |
| [Epic 4](../epics/PRD-FI-001/epic-4_dogfood-integration.md) | Ringspo tenant dogfood | 4 | CP 48 + CP 49 (E2E) |
| [Epic 5](../epics/PRD-FI-001/epic-5_b2b-adapters.md) | Klaviyo adapter & B2B docs (optional v1.1) | 5 | CP 48 (B2B) |

## 8. Principle compliance

- **SRP** — ingest, diff, recommend, events, API are separate modules (`facet_intelligence/ingestion`, `inventory`, `recommend`, `events`, `api`).
- **Multi-tenant isolation** — Principle 14 in scaffold; `tenant_id` on every table and query.
- **External service isolation** — SparkleScore + webhook/ESP behind `shared/services/` adapters.
- **Idempotency** — `event_id = hash(tenant, listing_id, trigger, date)`; ingest upserts on `listing_id`.
- **Deterministic recommend** — same inputs + same inventory snapshot → same rank order; LLM never in rank path.
- **Testing** — rule-first unit tests per `.cursor/rules/test-intent.mdc`.

## 9. Cross-references

| Topic | Document |
|-------|----------|
| Product vision (experience, email, trust) | `diamond-prices/docs/architecture/facet-intelligence-product-vision.md` |
| Repo boundaries | `diamond-prices/docs/architecture/platform-product-boundaries.md` |
| Stone input paths | `diamond-prices/docs/architecture/stone-input-paths.md` |
| Repo bootstrap megaprompt | `diamond-prices/docs/architecture/facet-intelligence-bootstrap-prompt.md` |
| Phase 8 consumer surfaces | `diamond-prices` PRD-009, `consumer-advisory-overview.md` |
| Email dispatch (CP 49) | `diamond-prices/docs/architecture/email-strategy.md` |
| SparkleScore scope fence | `sparklescoredata/docs/ARCHITECTURE.md` § What SparkleScore is not |
| Engagement strategy | `diamond-prices/docs/strategy/user-engagement-retention.md` |

## 10. Tech debt accepted (v1)

- Diamond-only modes implemented; `item_type` / `mode` enums carried but not built.
- Fancy shapes deferred (round-first aligned with SparkleScore MVP).
- Single-region deploy (Sevalla); no multi-region failover.
- Metering hooks only; no billing module.
