# Epic 4: Dogfood Integration — Ringspo / DHUK (PRD-FI-001)

**Checkpoints:** CP 48 (client), CP 49 (E2E events)
**Status:** not_started

**Prerequisites:** Follow the ordered checklist in [`diamond-prices/docs/operations/facet-intelligence-staging-e2e.md`](../../../../diamond-prices/docs/operations/facet-intelligence-staging-e2e.md) § Dogfood closure sequence. Wire `RINGSPO_US_WEBHOOK_URL` only after the FI webhook outbox fix (P0 #1) is deployed.

## Goal

Validate Facet Intelligence as `ringspo-us` tenant (wave 1); wire `diamond-prices` staging to consume events and call discover/recommend. Additional tenants (e.g. `diamondhunt-uk`) via config only.

## Stories (outline)

1. **4.1** — Onboard tenants in `config/tenants.py`; API keys + inventory source mapping.
2. **4.2** — `diamond-prices` Facet Intelligence HTTP client (`shared/services/facet_intelligence/` or equivalent).
3. **4.3** — Engagement layer webhook receiver for Facet Intelligence events (staging).
4. **4.4** — E2E checklist: cert-in → discover → shortlist → simulated disappearance → email payload with alternatives.

## Success

- Staging demonstrates full loop documented in `facet-intelligence-product-vision.md` (without production SES).
