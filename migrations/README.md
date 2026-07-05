# Migrations

Idempotent SQL migrations for the `facet_intelligence` PostgreSQL database.

Apply in order:

```bash
psql "$DATABASE_URL" -f migrations/001_tenants.sql
```

Every table must include `tenant_id`.
