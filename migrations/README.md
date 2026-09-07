# Migrations

Idempotent SQL migrations for the `facet_intelligence` PostgreSQL database.

Apply in order (TablePlus — not automated):

```bash
psql "$DATABASE_URL" -f migrations/001_tenants.sql
psql "$DATABASE_URL" -f migrations/002_tenant_listings.sql
psql "$DATABASE_URL" -f migrations/003_inventory_snapshots_and_events.sql
```

| Migration | Purpose |
|-----------|---------|
| `001_tenants.sql` | Tenant registry |
| `002_tenant_listings.sql` | Canonical listing upserts per tenant |
| `003_inventory_snapshots_and_events.sql` | Daily snapshots, miss tracking, event dedupe |

Every table must include `tenant_id`.
