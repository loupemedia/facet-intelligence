# Security Hardening

## Required environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `DB_USER` | Yes | PostgreSQL user for `facet_intelligence` database |
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `DB_HOST` | Yes | PostgreSQL host |
| `DB_PORT` | Yes | PostgreSQL port |
| `DB_NAME` | Yes | Database name (`facet_intelligence`) |
| `DB_SSLMODE` | No | Defaults to `require` |
| `FACET_INTELLIGENCE_API_KEY` | Staging+ | Bearer token for API requests |
| `SPARKLESCORE_API_URL` | Epic 3+ | SparkleScore base URL |
| `SPARKLESCORE_API_KEY` | Epic 3+ | SparkleScore API key |
| `RINGSPO_US_WEBHOOK_URL` | Epic 2+ | Engagement webhook for `ringspo-us` tenant events |
| `FACET_INTELLIGENCE_WEBHOOK_SECRET` | Epic 2+ | HMAC secret for `X-Facet-Intelligence-Signature` on outbound webhooks |

When adding a new env var: update this table before merging dependent code.

## Security checklist

- [ ] No secrets in git
- [ ] Parameterised SQL (`%s` placeholders only)
- [ ] Rollback on DB errors; connections returned to pool in `finally`
- [ ] Rate limits on public API endpoints
- [ ] Every query scoped by `tenant_id`
- [ ] Pre-commit + CI `detect-secrets` green
