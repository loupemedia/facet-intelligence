# Epic 2: Inventory Snapshot, Diff & Events (PRD-FI-001)

**Checkpoints:** CP 48 (signals), CP 49 (event consumer)
**Status:** in_progress — Stories 2.1–2.3 and 2.5 complete; 2.4 better-match stub (Epic 3)

## Goal

Daily per-tenant snapshots; disappearance, price-drop, and better-match detection; idempotent webhook events.

## Stories (outline)

1. **2.1** — Snapshot store + daily job (`shared.pipeline_date.pipeline_today()`).
2. **2.2** — Disappearance diff with configurable grace period (default 2–3 days).
3. **2.3** — Price-drop detection vs tenant price history.
4. **2.4** — **Better-match detection** — after sync, for watched anchors (from engagement webhook registration or tenant config), find new/updated listings that beat anchor on SparkleScore quality floor; emit `diamond.better_match`.
5. **2.5** — Event emitter + webhook adapter (`diamond.disappeared`, `diamond.price_dropped`, `diamond.better_match`).

### Story 2.5 — Webhook outbox contract (2026-09-10)

Implemented in `facet_intelligence/inventory/signals.py` and `scripts/F1_daily_inventory_signals.py`.

| Rule | Behaviour |
|------|-----------|
| Order | **POST webhook first**, then insert into `tenant_emitted_events` only after 2xx |
| No webhook URL | Log warning; **do not** dedupe (retry when `RINGSPO_US_WEBHOOK_URL` is set) |
| Delivery failure | Log error; **do not** dedupe (same-day retry keeps same `event_id`) |
| Dry-run (`--dry-run`) | Detect signals; **do not** dedupe (avoids blocking a later live run) |
| Snapshot | `capture_snapshot()` always runs in `finally` (delivery errors must not skip diff baseline) |
| F1 exit code | Non-zero when `events_delivery_failed` or `events_skipped_no_webhook` > 0 |

Cross-repo sequencing: [`diamond-prices/docs/operations/facet-intelligence-staging-e2e.md`](../../../../diamond-prices/docs/operations/facet-intelligence-staging-e2e.md) § Dogfood closure sequence.

## Success

- Staging run produces events when a seeded listing disappears, drops price, or a strictly better match appears; `event_id` dedupes replays after successful delivery.
