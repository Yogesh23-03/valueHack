# BizSim engine audit (Step 0)

Audit of the engine layer before the Person 1 refactor, the demo behaviour that
was frozen, and what was missing.

## What existed

| Area | File | State before |
|---|---|---|
| Simulation | `backend/app/engine/cascade.py` | One function `simulate()` with demo constants baked in |
| Actions | `backend/app/engine/actions.py` | `compare_actions(delay)` calling `simulate` with fixed flags |
| Analytics | — | did not exist |
| Pricing | `backend/app/engine/pricing.py` | empty file |
| Explanations | `backend/app/explain/reasons.py` | empty file |
| Models | `backend/app/models.py` | SQLModel rows only (Business, Supplier, Product, Customer) |
| API | `backend/app/main.py` | `/api/simulate/cascade`, `/api/actions/compare` returned the raw `simulate` dict |

## What was hard-coded inside `engine/`

`cascade.py` embedded the entire demo business:

- stock `{"fans": 36, "wiring": 54, "switches": 300}`
- demand `{"fans": 4, "wiring": 6, "switches": 15}`
- prices `{1900, 1200, 170}`, fixed cost `3000 + 1800`
- Supplier A restock day `8`, invoice `275000`, due day `23`
- Supplier C payable `70000`, due day `25`
- Verma order `20 fans + 30 wiring`, `74000`, target day `12`, +7 day terms
- opening cash `50000`

None of these could come from a `Business` object; nothing was unit-testable
without editing the function.

## What was missing

- No `Business`/`Product`/`Shock` input models, no adapters, so the engine could
  not run from a dict, the database, or CSV.
- No structured events, no causal links, no cascade chain.
- No explanations; `lost_rev` was hard-coded to `0` and `min_day` to `0`.
- No assumptions, no ranges, no scenario dispatcher (`cost_spike_pct` and
  `customer_late_days` were parameters but unused for explainability).
- No affordability, no risk rubric, no suggested action, no vendor hook.
- No `/api/pricing/whatif` route.
- No tests at all.

Known bugs in the old `simulate`: a failed payment did **not** deduct the amount
(so the gap size was invisible), `lost_rev` and `min_day` were always `0`, and
Verma was delivered from day 1 rather than from the target day.

## Frozen behaviour (characterization)

Full JSON responses were saved under `backend/tests/golden/`:

- `business.json`
- `cascade_baseline.json` (`delay = 0`)
- `cascade_delay14.json` (`delay = 14`)
- `actions_delay14.json`

`backend/tests/test_golden.py` asserts the legacy fields keep their names,
types and values, while the new fields are present alongside.

## Oracle reconciliation

The reference oracle table in the task brief was reproduced exactly by the new
engine for the real seed data. Two model facts were needed to match it and are
recorded in `docs/engine_decisions.md`:

1. the headline stock-out and lost-sales metrics are scoped to the disrupted
   supplier's products (fans and wiring), and
2. the initial cash is not itself a "lowest cash" candidate — the metric is the
   minimum of the daily timeline.

All ten oracle rows pass in `backend/tests/test_oracle.py` with the arithmetic
written in comments.
