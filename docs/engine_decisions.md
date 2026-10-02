# Engine decisions

Ambiguities resolved while building the engine, with the reasoning. Rule 8 of
the brief: pick the simplest reasonable option and record it here.

## 1. Headline stock-out and lost-sales metrics are scoped to the disrupted supply

**Decision.** `summary.stockout_day` and `summary.lost_sales_inr` count only
products supplied by the scenario's target supplier (default: the business's
`primary_supplier`, "Supplier A" in the demo). Lost sales for every product are
still available as `summary.lost_sales_all_products_inr`, and a `sales_lost`
event is emitted for each product.

**Why.** The reference oracle's lost-sales column is always an exact multiple of
₹14,800, which is one day of *fans + wiring* walk-in sales. In the demo,
switches (Supplier C) genuinely stock out on day 21 and stop earning revenue —
cash matches the oracle only when their revenue stops — but their lost sales are
not part of the headline metric. Scoping the headline to the affected supply
chain (recorded as the `lost_sales_scope` assumption) reproduces all ten oracle
rows exactly and matches the brief's own sentence: *"Walk-in sales of fans and
wiring stop for 12 days, which loses about ₹1,77,600."*

## 2. Lowest cash is the minimum of the daily timeline, not the opening cash

**Decision.** `summary.lowest_cash_inr` / `lowest_cash_day` are computed over
the day-by-day cash timeline only.

**Why.** Opening cash of ₹50,000 is never the minimum in the oracle: the
baseline row's lowest cash is ₹62,550 on day 1. Including the opening balance
would have made ₹50,000 on "day 0" the answer.

## 3. Failed payments are still deducted

**Decision.** When cash is below an amount due, the engine records a failed
payment *and* deducts the amount anyway.

**Why.** The brief requires it ("record a failed payment and still deduct it so
the gap size is visible"). It is what produces the oracle's lowest cash of
₹-1,71,600 on day 25.

## 4. Invoice due dates do not move with late delivery

**Decision.** The Supplier A invoice stays due on day 23 even when delivery
slips to day 22. Extensions are an explicit action
(`invoice_extension_days`).

**Why.** Stated in the brief and required by the oracle.

## 5. A customer early-payment discount accelerates payment

**Decision.** `early_discount_pct` reduces the order value by that percent and
moves payment to the **delivery day** (instead of the +7-day terms).

**Why.** The oracle row "14 days late + 3 percent early-payment discount from
Verma only" has a lowest cash of ₹-99,820 on day 25. That only reconciles if the
71,780 rupee payment arrives on delivery day (22): 87,650 helped the day-23
position, and the day-25 amount lands at -99,820 exactly. Without acceleration
the minimum would be worse in a different way.

## 6. Alternative vendor schedule

**Decision.** The new distributor replaces Supplier A's restock with: cost =
invoice × (1 − 15%), 50% advance on day 3, delivery on day 6, balance due 15
days after delivery (day 21). When `vendor_fails` is true, no stock arrives but
the advance and balance are still due.

**Why.** Given in the brief. The oracle requires the balance to remain due on
day 21 even when the vendor vanishes (failed payments on days 3, 21 and 25).

## 7. Cascade `failed_supplier_payment` step reports the last failure

**Decision.** The final cascade step's `day` is the last failed payment in the
run, not the first.

**Why.** The brief's expected chain ends with
`failed_supplier_payment` on **day 25** (Supplier C), even though the Supplier A
invoice fails first on day 23. Day 25 is the downstream cascade failure.

## 8. Risk rubric (heuristic)

The action risk score is a transparent, tunable heuristic — **not** a
probability. Factors and points:

| Factor | Points |
|---|---|
| Cash goes below zero | +2 |
| Each failed payable | +1 |
| A required payment is unaffordable on its day | +2 |
| Needs a counterparty to agree | +1 |
| Unmitigated stock-out of 5 or more days | +1 |
| Vendor band red / amber / unknown | +3 / +1 / +1 |

Levels: score 0–1 **Low**, 2–3 **Medium**, 4+ **High**. Every factor is
returned with a plain-language reason in `risk.factors`.

## 9. Suggested action rule

**Decision.** Among actions with **no** cash gap, mark the one with the lowest
risk score; break ties by the highest end cash. If no action avoids the gap,
mark none and say so in `suggested_reason` on every action.

**Why.** Required by the brief. For the 14-day delay the extension wins: it
avoids the gap with the lowest risk and keeps the full ₹74,000 from Verma
(the combined extension + discount gives ₹2,220 away for no extra benefit).

## 10. Price elasticity is an assumption

**Decision.** Elasticity bands are low −0.4, base −0.7, high −1.2, returned with
`source: "assumed"`.

**Why.** Small-business data rarely contains enough price variation to estimate
elasticity, so the brief labels it an assumption. Break-even demand drop uses
`1 − m/(m + dp)` with `m` the current unit margin and `dp` the price change in
rupees.

## 11. Error format

All engine errors are raised as `EngineError` and serialised as
`{"code", "message"}` with status 422 for invalid input and 404 for unknown
entities. Codes: `INVALID_SHOCK`, `UNKNOWN_SUPPLIER`, `UNKNOWN_CUSTOMER`,
`UNKNOWN_PRODUCT`, `MAGNITUDE_OUT_OF_RANGE`, `ELASTICITY_OUT_OF_RANGE`,
`INVALID_INPUT`.
