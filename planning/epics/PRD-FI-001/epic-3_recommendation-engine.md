# Epic 3: Recommendation & Discover API (PRD-FI-001)

**Checkpoint:** CP 48
**Status:** complete — Stories 3.1–3.5 shipped

## Goal

Deterministic recommend engine with SparkleScore + vanilla backends; anchor and intent-first APIs.

## Stories (outline)

1. **3.1** — Scoring backend interface + SparkleScore client adapter.
2. **3.2** — Vanilla scorer fallback (4Cs + proportions + price-vs-market).
3. **3.3** — `POST /v1/recommend` — substitute_diamond, quality floor, categories.
4. **3.4** — `POST /v1/discover` — intent-first, no anchor; `buyer_intent` + constraints.
5. **3.5** — `reason_codes[]` + headline generation (deterministic templates, not LLM).

## Success

- Discover and recommend return ≤5 ranked alternatives with scores; quality floor rejects worse substitutes.
