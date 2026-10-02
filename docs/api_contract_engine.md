# Engine API contract (Person 1 → Person 3 & Person 4)

Frozen shapes for the four engine surfaces. Person 3 builds the "Why?" panel,
assumptions box, cascade map and sliders from this file. Person 4 reads the
`VendorRisk` signature here.

Conventions: money fields are plain numbers with an `_inr` suffix; text is
formatted with Indian grouping (`₹1,77,600`) by `explain.reasons.format_inr`.
Same input → same output (deterministic). "Estimate" wording throughout.

Error format for every engine error (status 422 invalid input, 404 unknown
entity):

```json
{"code": "UNKNOWN_SUPPLIER", "message": "No supplier 'nope' in this business."}
```

Error codes: `INVALID_SHOCK`, `UNKNOWN_SUPPLIER`, `UNKNOWN_CUSTOMER`,
`UNKNOWN_PRODUCT`, `MAGNITUDE_OUT_OF_RANGE`, `ELASTICITY_OUT_OF_RANGE`,
`INVALID_INPUT`.

---

## 1. `POST /api/simulate/cascade`

Request (all optional; legacy fields preserved):

```json
{
  "delay": 14,
  "horizon": 30,
  "ext_a": 0,
  "ext_c": 0,
  "early_discount": 0.0,
  "alt_supplier": false,
  "alt_fails": false,
  "cost_spike_pct": 0.0,
  "customer_late_days": 0,
  "demand_band_pct": 20,
  "scenario": {"type": "supplier_delay", "target": "A", "magnitude": 14, "duration_days": null}
}
```

`scenario.type` is one of `supplier_delay`, `customer_delay`, `cost_spike`,
`demand_shock`. `target` accepts an id (`sup_a`), a name (`Supplier A`) or a
letter (`A`). `demand_band_pct` is 0–50 (default 20).

Response top level (trimmed, `delay = 14`):

```json
{
  "stockout": 10,
  "lost_rev": 177600.0,
  "first_negative_day": 23,
  "min_cash": -171600.0,
  "min_day": 25,
  "failed": [
    {"name": "Supplier A invoice", "day": 23},
    {"name": "Supplier C invoice", "day": 25}
  ],
  "delivered": true,
  "end_cash": -47600.0,
  "cash_timeline": [62550.0, 75100.0, "...30 numbers..."],
  "stock_timeline": [{"fans": 32.0, "wiring": 48.0, "switches": 285.0}, "..."],
  "scenario": {
    "type": "supplier_delay", "target": "sup_a", "target_name": "Supplier A",
    "magnitude": 14.0, "label": "legacy", "switch_vendor": false,
    "vendor_fails": false, "early_discount_pct": 0.0,
    "invoice_extension_days": 0, "payable_extension_days": 0, "demand_multiplier": 1.0
  },
  "summary": {
    "stockout_day": 10,
    "lost_sales_inr": 177600.0,
    "lost_sales_all_products_inr": 203100.0,
    "first_negative_day": 23,
    "lowest_cash_inr": -171600.0,
    "lowest_cash_day": 25,
    "end_cash_inr": -47600.0,
    "failed_payments_count": 2,
    "order_delay_days": 10,
    "customer_payment_day": 29
  },
  "cascade_chain": [
    {"step": "supplier_delay", "status": "triggered", "day": 8, "title": "Supplier delay",
     "detail": "Supplier A's restock slips from day 8 to day 22."},
    {"step": "inventory_shortage", "status": "triggered", "day": 10, "...": "..."},
    {"step": "delayed_orders", "status": "triggered", "day": 22, "...": "..."},
    {"step": "customer_payment_delay", "status": "triggered", "day": 29, "...": "..."},
    {"step": "cash_gap", "status": "triggered", "day": 23, "...": "..."},
    {"step": "failed_supplier_payment", "status": "triggered", "day": 25, "...": "..."}
  ],
  "events": [
    {"id": "ev001", "day": 8, "type": "restock_slipped", "entity": "Supplier A",
     "values": {"scheduled_day": 8.0, "actual_day": 22.0, "days_late": 14.0},
     "cause_ids": [], "severity": "warning"}
  ],
  "timeline": {"cash": [62550.0, "..."], "stock": [{"fans": 32.0, "...": 0.0}, "..."]},
  "explanations": [
    {"metric_id": "stockout_day", "label": "First stock-out day", "value": 10, "unit": "day",
     "sentence": "Fans and Wiring coils run out on day 10 because Supplier A's restock slips from day 8 to day 22.",
     "event_ids": ["ev003"]}
  ],
  "assumptions": [
    {"id": "supplier_invoice_date_fixed", "text": "The supplier invoice date does not move when delivery is late, so the Supplier A invoice stays due on day 23.",
     "value": 23.0, "unit": "day", "editable": false, "source": "demo_data"}
  ],
  "ranges": {
    "runs": [
      {"case": "low", "demand_multiplier": 0.8, "metrics": {"stockout_day": 10, "lost_sales_inr": 148000.0,
        "first_negative_day": 22, "lowest_cash_inr": -183440.0, "lowest_cash_day": 24, "end_cash_inr": -38600.0}},
      {"case": "base", "demand_multiplier": 1.0, "metrics": {"...": "..."}},
      {"case": "high", "demand_multiplier": 1.2, "metrics": {"...": "..."}}
    ],
    "metrics": {
      "for each of stockout_day, lost_sales_inr, first_negative_day, lowest_cash_inr, lowest_cash_day, end_cash_inr":
        {"min": -183440.0, "base": -171600.0, "max": -159760.0, "min_case": "low", "max_case": "high"}
    },
    "range_note": "Across demand 20 percent lower to 20 percent higher, cash first goes below zero between day 22 and day 24."
  },
  "meta": {"engine_version": "1.0.0", "horizon_days": 30, "deterministic": true, "shock_type": "supplier_delay"}
}
```

Notes for Person 3:

- The legacy fields (`stockout`, `lost_rev`, `first_negative_day`, `min_cash`,
  `min_day`, `failed`, `delivered`, `end_cash`, `cash_timeline`,
  `stock_timeline`) are unchanged. `events` is now the **structured** list.
- Every key in `summary` has a matching `explanations[].metric_id`; the sentence
  always contains the metric's own formatted value.
- `cascade_chain[].status` ∈ `triggered` | `avoided` | `not_reached`.
- `unit` ∈ `inr` | `day` | `count`; use `format_inr` when `unit == "inr"`.
- `assumptions[].source` ∈ `demo_data` | `assumed` | `user`.

---

## 2. `POST /api/actions/compare`

Request: `{"delay": 14}`. Response is keyed by action id
(`do_nothing`, `ask_extension`, `early_discount`, `switch_vendor`, `combined`,
`switch_supplier`). Each value is the full cascade response **plus**:

```json
{
  "id": "switch_supplier",
  "label": "Switch to the new distributor",
  "delta_vs_do_nothing": {
    "stockout_day": {"base": 10, "action": 30, "delta": 20},
    "lost_sales_inr": {"base": 177600.0, "action": 14800.0, "delta": -162800.0},
    "first_negative_day": {"base": 23, "action": 3, "delta": -20},
    "lowest_cash_inr": {"base": -171600.0, "action": -29225.0, "delta": 142375.0},
    "end_cash_inr": {"base": -47600.0, "action": 156450.0, "delta": 204050.0},
    "failed_payments_count": {"base": 2, "action": 1, "delta": -1}
  },
  "tradeoff": "Still leaves cash below zero on day 3. cuts lost sales by ₹1,62,800. but needs ₹29,225 more cash than is available on the payment day. and raises end cash by ₹2,04,050.",
  "affordable": false,
  "shortfall_inr": 29225.0,
  "requires_counterparty_agreement": false,
  "risk": {
    "level": "High", "score": 6,
    "factors": [
      {"points": 2, "reason": "Cash goes below zero on day 3."},
      {"points": 1, "reason": "1 supplier payment(s) cannot be made."},
      {"points": 2, "reason": "A required payment is not affordable on its day."},
      {"points": 1, "reason": "The vendor is not verified."}
    ]
  },
  "suggested": false,
  "suggested_reason": "Suggested: Ask Supplier A for an extension. It avoids the cash gap ...",
  "vendor_risk": {"score": -1, "band": "unknown", "reasons": ["Vendor check not connected"]},
  "exposure_inr": null,
  "vendor_fails_result": {"summary": {"lowest_cash_inr": -213550.0, "...": "..."}}
}
```

Risk rubric: cash gap +2; each failed payable +1; unaffordable +2; needs
counterparty +1; unmitigated stock-out ≥5 days +1; vendor red +3 / amber +1 /
unknown +1. Level: 0–1 Low, 2–3 Medium, 4+ High. Exactly one action has
`suggested: true`, or none with an honest note in `suggested_reason`.

For the 14-day delay: `do_nothing` High, `ask_extension` Medium
(`requires_counterparty_agreement: true`) and suggested, `early_discount` still
has a gap, `combined` has no gap, `switch_supplier` unaffordable with a ₹29,225
shortfall.

---

## 3. `POST /api/pricing/whatif`

Request:

```json
{"product_id": "fans", "price_change_pct": 10, "elasticity": -0.7, "horizon_days": 30}
```

Response:

```json
{
  "product": "Fans", "product_id": "fans",
  "current_price_inr": 1900.0, "new_price_inr": 2090.0, "price_change_pct": 10.0,
  "elasticity": {"low": -0.4, "base": -0.7, "high": -1.2},
  "demand_multiplier": {"low": 0.96, "base": 0.93, "high": 0.88},
  "unit_margin_inr": 500.0, "new_unit_margin_inr": 690.0,
  "profit_inr": {"low": 79488.0, "base": 77004.0, "high": 72864.0},
  "profit_change_inr": {"low": 21488.0, "base": 19004.0, "high": 14864.0},
  "breakeven_demand_drop_pct": 27.54,
  "horizon_days": 30,
  "curve": [{"price_change_pct": -20, "profit_inr": {"low": 0.0, "base": 0.0, "high": 0.0},
             "demand_multiplier": {"low": 1.08, "base": 1.14, "high": 1.24}}, "… 21 points from -20 to +20 step 2 …"],
  "sentence": "A 10% price rise for Fans keeps profit level if demand falls by no more than 27.54% (unit margin 500 to 690 rupees), assuming an elasticity of -0.7.",
  "assumptions": [
    {"id": "price_elasticity", "text": "…", "value": -0.7, "unit": "elasticity",
     "editable": true, "source": "assumed"}
  ]
}
```

`elasticity` must be in [-3.0, 0.0] or the endpoint returns
`ELASTICITY_OUT_OF_RANGE` (422). Elasticity is labelled an assumption because
small-business data rarely supports estimating it. The `curve` is precomputed so
the slider needs no round trip.

---

## 4. `GET /api/business` (analytics block, additive)

```json
{
  "name": "Sharma Hardware and Electricals",
  "cash": 50000,
  "analytics": {
    "dependency_shares": {
      "products": [
        {"product": "Fans", "product_id": "fans", "suppliers": [{"name": "Supplier A", "share_pct": 100.0}]}
      ],
      "supplier_dependency": [
        {"supplier": "Supplier A", "supplier_id": "sup_a", "stock_value_share_pct": 87.7,
         "purchase_value_share_pct": 79.7, "concentration": "high"}
      ]
    },
    "stock_cover": [
      {"product": "Fans", "product_id": "fans", "stock_units": 36.0, "daily_demand": 4.0,
       "cover_days": 9.0, "next_restock_day": 8, "days_to_stockout": 9.0, "status": "watch"}
    ],
    "attention_inputs": [
      {"kind": "supplier_concentration", "entity": "Supplier A", "severity": "warning",
       "day": null, "evidence": "Supplier A carries 79.7 percent of purchase value."}
    ]
  }
}
```

`status` ∈ `safe` | `watch` | `critical`. `concentration` ∈ `high` (≥50%) |
`medium` (30–49%) | `low`. `attention_inputs` are for Person 2 to merge into
`/api/attention`.

---

## 5. Vendor hook (Person 4)

In `app/engine/actions.py`:

```python
from typing import Literal, TypedDict

class VendorRisk(TypedDict):
    score: int                                   # 0..100
    band: Literal["green", "amber", "red", "unknown"]
    reasons: list[str]

def get_vendor_risk(vendor_identifier: str) -> VendorRisk:
    """Stub: returns band 'unknown'. Person 4 replaces the body by calling signals.vendor."""
    return {"score": -1, "band": "unknown", "reasons": ["Vendor check not connected"]}
```

Person 4 only replaces the body of `get_vendor_risk`; the signature and the
`vendor_risk` field on the `switch_supplier` action are frozen. A red band adds
+3 risk, amber +1, unknown +1, and a red band also fills `exposure_inr` (the
advance at risk) and `vendor_fails_result`.
