# Engineering Principles

Facet Intelligence follows the same fourteen principles as `diamond-prices` and `sparklescoredata`. Full rationale and examples: port from `../diamond-prices/docs/ENGINEERING_PRINCIPLES.md` when syncing platform standards.

**Facet Intelligence-specific enforcement:**

| Principle | FI application |
|-----------|----------------|
| **5 Idempotency** | `listing_id` upserts; `event_id` dedupe on webhooks |
| **12 DB efficiency** | Batch ingest via `execute_values`; no per-row diff loops at feed scale |
| **13 External service isolation** | SparkleScore, webhooks, Klaviyo behind `shared/services/` |
| **14 Multi-tenant isolation** | `tenant_id` on every table, query, and event — never inferred from API key alone without lookup |

Compliance checklist: same as platform doc. Test intent: `.cursor/rules/test-intent.mdc`.
