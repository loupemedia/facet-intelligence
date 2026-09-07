# Test fixtures

Raw feed rows for listing normalisation (Story 1.2). Scenarios mirror
`diamond-prices/docs/architecture/stone-identity-keys.md` homonym rules.

| File | Scenario |
|------|----------|
| `listing_certed_bn.json` | Certed GIA stone at Blue Nile |
| `listing_certed_ja_same_cert.json` | Same cert at James Allen (variant formatting) |
| `listing_uncerted_sku.json` | Brilliant Earth-style SKU-only row |
| `listing_fingerprint_only.json` | No cert or SKU (needs retailer added in test) |
| `feed_us_sample.csv` | CSV feed with in-pool + Ritani (out of pool) |
| `feed_us_json.json` | JSON sync body with in-pool + RT (out of pool) |
| `stone_export_us_sample.json` | R1 stone-layer export shape (display-name retailer) |
