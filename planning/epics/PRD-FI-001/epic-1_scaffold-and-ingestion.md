# Epic 1: Scaffold, Tenancy & Ingestion (PRD-FI-001)

**Checkpoint:** CP 48 (foundation)
**Status:** complete — Stories 1.1–1.4 done; Epic 2 next

## Goal

Bootstrap the `facet-intelligence` repository and ingest first tenant inventory into a canonical listing schema.

## Stories (outline)

1. **1.1** — Repo scaffold per `facet-intelligence-bootstrap-prompt.md` (CI, principles, `facet_intelligence` DB migrations with `tenant_id`).
2. **1.2** — Canonical listing normalisation + stable `listing_id` generation.
3. **1.3** — Feed loader (CSV/JSON) + country-pool adapter for `ringspo-us` tenant.
4. **1.4** — `POST /v1/inventory/sync` + `inventory.synced` event stub.

## Success

- `ringspo-us` staging sync accepts a retailer pool slice and persists tenant-scoped rows idempotently.
