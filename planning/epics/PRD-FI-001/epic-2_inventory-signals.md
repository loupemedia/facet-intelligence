# Epic 2: Inventory Snapshot, Diff & Events (PRD-FI-001)

**Checkpoints:** CP 48 (signals), CP 49 (event consumer)
**Status:** not_started

## Goal

Daily per-tenant snapshots; disappearance, price-drop, and better-match detection; idempotent webhook events.

## Stories (outline)

1. **2.1** — Snapshot store + daily job (`shared.pipeline_date.pipeline_today()`).
2. **2.2** — Disappearance diff with configurable grace period (default 2–3 days).
3. **2.3** — Price-drop detection vs tenant price history.
4. **2.4** — **Better-match detection** — after sync, for watched anchors (from engagement webhook registration or tenant config), find new/updated listings that beat anchor on SparkleScore quality floor; emit `diamond.better_match`.
5. **2.5** — Event emitter + webhook adapter (`diamond.disappeared`, `diamond.price_dropped`, `diamond.better_match`).

## Success

- Staging run produces events when a seeded listing disappears, drops price, or a strictly better match appears; `event_id` dedupes replays.
