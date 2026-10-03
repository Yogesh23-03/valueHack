# BizSim — Business Continuity Intelligence

BizSim is a **fire-drill cascade simulator** for small businesses. It shows how
one disruption — a late supplier, a late customer, a cost spike — propagates
through a business into a stock-out, delayed orders, a customer payment delay, a
cash-flow gap, and finally an unpaid supplier.

> **Philosophy: BizSim gives estimates, not predictions. The tool suggests; the
> owner decides.** Every figure comes from a deterministic 30-day simulation over
> **synthetic demo data**, and every explanation says so.

Built for SMVIT ValueHack 2026. MVP target 8 Oct 2026, feature freeze 6 Oct 2026.

---

## 1. The problem, and where BizSim answers it

| Chain in the problem statement | Where BizSim answers it |
|---|---|
| A supplier is late | `scenario.type: supplier_delay` — Fire Drill controls, `/api/simulate/cascade` |
| Inventory shortage | `stock_timeline`, `summary.stockout_day`, stock chart |
| Delayed orders | `cascade_chain` step `delayed_orders`, event `order_delayed` |
| Customer payment delay | `cascade_chain` step `customer_payment_delay`, `summary.customer_payment_day` |
| Cash-flow gap | `cash_timeline`, `summary.first_negative_day` / `lowest_cash_inr`, chart markers |
| Unpaid supplier | `cascade_chain` step `failed_supplier_payment`, `failed[]`, risk factor “each failed payable” |
| “What could I do about it?” | `/api/actions/compare` — six actions with deltas, risk, affordability and one suggested action |
| “Why does it say that?” | `explanations[]` — one plain sentence per metric, linked to `events[]` |

---

## 2. Current features (strict status)

Status is judged from the code on disk, not from intent.

| Feature | Status | Where it lives |
|---|---|---|
| Cascade engine, day-by-day simulation | **Implemented** | `backend/app/engine/sim.py`, `cascade.py` |
| Data-driven `Business` model + adapters (dict or DB) | **Implemented** | `engine/models.py`, `engine/adapters.py` |
| Three scenario types (supplier delay, customer delay, cost spike) + demand shock dispatcher | **Implemented** | `main.py` (`ScenarioShock`), `engine/cascade.py` |
| Structured events with ids, days, severity, cause links | **Implemented** | `engine/sim.py`, `explain/reasons.py` |
| Six-step cascade chain with per-step status/day/detail | **Implemented** | `explain/reasons.py` |
| Plain-language explanations, one per metric | **Implemented** | `explain/reasons.py` |
| Assumptions list with `source` tags (`demo_data`/`assumed`/`user`) | **Implemented** | `explain/reasons.py` |
| Demand ranges (low/base/high runs + min/base/max + note) | **Implemented** | `engine/ranges.py` |
| Action comparison: 6 actions, deltas, tradeoff, affordability, risk rubric, suggestion | **Implemented** | `engine/actions.py` |
| Vendor-risk hook on `switch_supplier` | **Stub** — `get_vendor_risk()` returns band `unknown`, score −1 | `engine/actions.py` (`VendorRisk` signature frozen for Person 4) |
| Price what-if with elasticity bands, curve and break-even | **Implemented** | `engine/pricing.py`, `routers/engine.py` |
| Supplier dependency shares + stock cover analytics | **Implemented** | `engine/analytics.py` |
| Attention inputs computed from the engine | **Implemented** | `engine/analytics.py` → `analytics.attention_inputs` |
| `/api/attention` list | **Mock** — hard-coded list in the route (Person 2 scope) | `main.py` |
| Scenario parser (“describe it in plain words”) | **Mock** — regex only, no LLM call; always returns a supplier delay | `signals/llm.py` |
| Vendor trust check | **Mock** — rule on the name string (“New Distributor” → red 32, anything else → green 85) | `signals/vendor.py` |
| GSTIN checksum / registry lookup | **Not implemented** — empty file | `signals/gstin.py` |
| Bill scan (invoice extraction) | **Stub** — the route returns a fixed sample; no parsing | `main.py`, `signals/bills.py` (empty) |
| Report PDF (`GET /api/report`) | **Stub** — real PDF bytes, but the text is hard-coded and does **not** use engine output | `explain/report.py` |
| Forecast endpoint | **Not implemented** — returns `{"forecast": [], "mape": 0.05}` | `engine/forecast.py` (empty), `main.py` |
| Anomaly detection | **Not implemented** — returns `[]` | `engine/anomaly.py` (empty), `main.py` |
| CSV business upload / `/api/business/load` | **Planned** — endpoint does not exist, so the UI does not fake it | — |
| Fire Drill screen (controls, cascade map, timelines, why panel, assumptions, ranges, actions) | **Implemented** | `frontend/app/fire-drill/page.tsx`, `frontend/components/fire-drill/*` |
| Dashboard (KPIs, dependency bars, stock cover, attention) | **Implemented** | `frontend/app/dashboard/page.tsx` |
| Price what-if screen | **Implemented** | `frontend/app/pricing/page.tsx` |
| Report screen (engine numbers + PDF download) | **Implemented** | `frontend/app/report/page.tsx` |
| Vendor check screen | **Implemented** (mock data, labelled), links into the Fire Drill | `frontend/app/vendor-check/page.tsx` |
| Bill scan screen | **Implemented** UI wired to the stub endpoint, labelled “demo stub output” | `frontend/app/bill-scan/page.tsx` |
| Automated backend tests | **Implemented** — 50 tests | `backend/tests/` |
| Automated UI tests (Playwright etc.) | **Not implemented** — manual browser checks only | — |

---

## 3. Visual verification

`docs/screenshots/demo-walkthrough.webm` is a real recording captured from the
running app (Fire Drill load, explanation → event highlight, scrolling, and
navigation). PNG screenshots were **not** produced: the in-app browser tool used
for verification renders images inline and does not write files to disk, so no
screenshot files are invented here. The full list of executed UI checks (and
which were not executed) is in `docs/BizSim_Engineering_Report.md`.

---

## 4. How it works

**Data flow for one Fire Drill**

```
Fire Drill controls ──► POST /api/simulate/cascade ──► engine.simulate()
   supplier delay /                          │            │
   customer delay /                          │            └─► events[] ─► cascade_chain[]
   cost spike, target,                       │                         └─► explanations[]
   magnitude, demand band (±0–50%)           │                         └─► assumptions[]
                                             │                         └─► ranges[] (3 runs)
                            POST /api/actions/compare ──► 6 actions + risk + suggestion
```

The frontend never calculates a business figure. It formats (`₹1,71,600`,
`Day 23`) and draws what the API returns.

**The day-by-day engine loop** (`engine/sim.py`): for each day 1…30 it receives
scheduled stock, delivers orders that stock allows, sells walk-in demand up to
available stock, collects receivables that are due, pays payables that are due
(recording a failed payment **and still deducting it** so the gap size is
visible), and records structured events.

**Events → cascade → explanations.** The run emits `events[]` (`ev001`…: day,
type, entity, values, `cause_ids`, severity). `explain/reasons.py` folds them
into the fixed six-step `cascade_chain` (each step `triggered`, `avoided` or
`not_reached`) and into `explanations[]`, one sentence per metric, each carrying
the `event_ids` that caused it — that is how the UI can highlight the events
behind a number.

**Assumptions and ranges.** Every run returns its assumptions with a `source`
(`demo_data` from `seed.py`, `assumed` for modelling choices, `user` for the
horizon) and whether the owner can edit them. `engine/ranges.py` re-runs the
scenario at ±`demand_band_pct` (default 20, max 50) and returns the three runs,
min/base/max per metric, and a plain `range_note`.

**Action risk rubric** (a transparent heuristic, **not** a probability):

| Factor | Points |
|---|---|
| Cash goes below zero | +2 |
| Each failed payable | +1 |
| A required payment is unaffordable on its day | +2 |
| Needs a counterparty to agree | +1 |
| Unmitigated stock-out of 5+ days | +1 |
| Vendor band red / amber / unknown | +3 / +1 / +1 |

Score 0–1 **Low**, 2–3 **Medium**, 4+ **High**, with a reason per factor.
**Suggestion rule:** among actions with no cash gap, pick the lowest risk score,
breaking ties by highest end cash; if none avoids the gap, suggest nothing and
say so.

**Price what-if.** `profit = units × unit margin` where demand responds as
`units × (1 + elasticity × price_change)`, shown for elasticity low −0.4, base
−0.7, high −1.2. Break-even demand drop is `1 − m / (m + Δp)` with `m` the unit
margin and `Δp` the rupee price change. A 21-point curve (−20%…+20%) is
precomputed so the UI slider needs no round trip. **Elasticity is an assumption**
(returned with `source: "assumed"`), because small-business data rarely supports
estimating it.

**The LLM's role and its limits.** There is no LLM in this build. The
“plain-words” box calls `signals/llm.py`, a regular-expression parser that reads
a day count and returns `{"type": "supplier_delay", "target": "A", "days": N}`.
Explanations are written by templates in `explain/reasons.py` from computed
values. Neither ever produces a number.

---

## 5. Demo business and demo scenario (verified output)

**Business:** Sharma Hardware and Electricals — synthetic data, defined only in
`backend/app/seed.py` (`DEMO_BUSINESS`). Cash ₹50,000; fixed costs ₹3,000 + other
supplies ₹1,800 per day; fans (36 in stock, 4/day, ₹1,900), wiring coils (54,
6/day, ₹1,200), switches (300, 15/day, ₹170); Supplier A restock day 8,
invoice ₹2,75,000 due day 23; Supplier C payable ₹70,000 due day 25; Verma
Contractors order ₹74,000, target day 12, +7-day terms.

**Demo scenario:** Supplier A is 14 days late.

Verified headline output (`delay = 14`):

| Metric | Value |
|---|---|
| First stock-out day | **Day 10** |
| Lost walk-in sales (disrupted supplier's products) | **₹1,77,600** (all products ₹2,03,100) |
| First day cash is below zero | **Day 23** |
| Lowest cash | **₹-1,71,600** on day 25 |
| Failed payments | **2** — Supplier A invoice day 23, Supplier C invoice day 25 |
| End cash | ₹-47,600 |

Action comparison for the same scenario (all figures from the engine):

| Action | Risk | Lowest cash | End cash | Notes |
|---|---|---|---|---|
| Do nothing | High | ₹-1,71,600 | ₹-47,600 | 2 failed payments |
| **Ask Supplier A for an extension** | **Medium** | **₹62,550** | **₹2,27,400** | **Suggested**; avoids the gap; needs counterparty agreement |
| Offer Verma an early-payment discount | High | ₹-99,820 | ₹-49,820 | still has a gap |
| Extension plus discount | Medium | ₹62,550 | ₹2,25,180 | avoids the gap; gives away ₹2,220 |
| Switch to the new distributor | High | ₹-29,225 | ₹1,56,450 | stock-out moves to day 30; **not affordable**, ₹29,225 shortfall |
| Switch to the new distributor (vanishes) | High | ₹-2,13,550 | ₹-2,13,550 | 3 failed payments |

---

## 6. API reference

FastAPI app (`backend/app/main.py`). Interactive docs at `http://localhost:8000/docs`.
All money fields are plain numbers with an `_inr` suffix; formatted text uses
Indian grouping (`₹1,77,600`).

| Method | Path | Purpose | Request | Key response fields |
|---|---|---|---|---|
| GET | `/health` | Liveness | — | `ok`, `version` |
| GET | `/api/business` | Business + analytics | — | `name`, `cash`, `analytics.{dependency_shares, stock_cover, attention_inputs}` |
| GET | `/api/attention` | Attention list (hard-coded stub) | — | `[{id, text, icon}]` |
| POST | `/api/simulate/cascade` | Run the cascade | `delay`, `horizon`, `ext_a`, `ext_c`, `early_discount`, `alt_supplier`, `alt_fails`, `cost_spike_pct`, `customer_late_days`, `demand_band_pct` (0–50), `scenario{type,target,magnitude,duration_days}` | legacy fields + `summary`, `cascade_chain`, `events`, `explanations`, `assumptions`, `ranges`, `timeline`, `meta` |
| POST | `/api/actions/compare` | Six actions + risk + suggestion | `{delay}` | one entry per action id (each a full cascade plus `delta_vs_do_nothing`, `tradeoff`, `risk`, `affordable`, `shortfall_inr`, `requires_counterparty_agreement`, `suggested`, `suggested_reason`, `vendor_risk`, `exposure_inr`, `vendor_fails_result`) |
| POST | `/api/pricing/whatif` | Price change on profit | `product_id`, `price_change_pct`, `elasticity` (−3…0), `horizon_days` | `elasticity`, `demand_multiplier`, `profit_inr`, `profit_change_inr`, `breakeven_demand_drop_pct`, `curve[21]`, `sentence`, `assumptions` |
| POST | `/api/scenario/parse` | Plain words → controls (regex) | `{text}` | `{type, target, days}` |
| POST | `/api/vendor/check` | Vendor trust (mock) | `{name, gstin, pan}` | `{score, badge, reasons[]}` |
| POST | `/api/bill/scan` | Invoice extraction (stub) | multipart `file` | fixed sample `{supplier, items[], due_date}` |
| GET | `/api/report` | PDF report (hard-coded text) | — | `application/pdf` stream |
| GET | `/api/forecast` | Not implemented | — | `{"forecast": [], "mape": 0.05}` |
| GET | `/api/anomalies` | Not implemented | — | `[]` |

**Error format** (status 422 invalid input, 404 unknown entity):

```json
{"code": "UNKNOWN_SUPPLIER", "message": "No supplier 'nope' in this business."}
```

Codes: `INVALID_SHOCK`, `UNKNOWN_SUPPLIER`, `UNKNOWN_CUSTOMER`, `UNKNOWN_PRODUCT`,
`MAGNITUDE_OUT_OF_RANGE`, `ELASTICITY_OUT_OF_RANGE`, `INVALID_INPUT`. The frontend
maps these to friendly sentences and never shows a stack trace.

### Real request and response examples

All snippets below are trimmed from the live captures in `docs/samples/`.

**14-day Supplier A delay** — `POST /api/simulate/cascade`

```json
{"delay": 14, "demand_band_pct": 20,
 "scenario": {"type": "supplier_delay", "target": "A", "magnitude": 14}}
```

```json
{"stockout": 10, "lost_rev": 177600.0, "first_negative_day": 23,
 "min_cash": -171600.0, "min_day": 25, "end_cash": -47600.0,
 "failed": [{"name": "Supplier A invoice", "day": 23},
            {"name": "Supplier C invoice", "day": 25}],
 "summary": {"stockout_day": 10, "lost_sales_inr": 177600.0,
   "lost_sales_all_products_inr": 203100.0, "first_negative_day": 23,
   "lowest_cash_inr": -171600.0, "lowest_cash_day": 25, "end_cash_inr": -47600.0,
   "failed_payments_count": 2, "order_delay_days": 10, "customer_payment_day": 29},
 "cascade_chain": [{"step": "supplier_delay", "status": "triggered", "day": 8,
   "title": "Supplier delay", "detail": "Supplier A's restock slips from day 8 to day 22."}],
 "explanations": [{"metric_id": "stockout_day", "label": "First stock-out day",
   "value": 10, "unit": "day",
   "sentence": "Fans and Wiring coils run out on day 10 because Supplier A's restock slips from day 8 to day 22.",
   "event_ids": ["ev002", "ev003"]}],
 "ranges": {"metrics": {"stockout_day": {"min": 8, "base": 10, "max": 12,
    "min_case": "high", "max_case": "low"}},
   "range_note": "Across demand 20 percent lower to 20 percent higher, cash first goes below zero on day 23 in every case."}}
```

**Action comparison** — `POST /api/actions/compare` with `{"delay": 14}`

```json
{"ask_extension": {
  "id": "ask_extension", "label": "Ask Supplier A for an extension",
  "suggested": true,
  "suggested_reason": "Suggested: Ask Supplier A for an extension. It avoids the cash gap with the lowest risk score (2) and the highest end cash among those options.",
  "affordable": true, "shortfall_inr": null, "requires_counterparty_agreement": true,
  "delta_vs_do_nothing": {"lowest_cash_inr": {"base": -171600.0, "action": 62550.0, "delta": 234150.0},
                          "end_cash_inr": {"base": -47600.0, "action": 227400.0, "delta": 275000.0}},
  "risk": {"level": "Medium", "score": 2,
    "factors": [{"points": 1, "reason": "Needs the counterparty to agree."},
                {"points": 1, "reason": "An unmitigated stock-out lasts 5 or more days."}]},
  "tradeoff": "Avoids the cash gap. does not change the stock-out. and raises end cash by ₹2,75,000. and needs the counterparty to agree."},
 "switch_supplier": {
  "id": "switch_supplier", "label": "Switch to the new distributor",
  "affordable": false, "shortfall_inr": 29225.0,
  "vendor_risk": {"score": -1, "band": "unknown", "reasons": ["Vendor check not connected"]},
  "exposure_inr": null}}
```

**Price what-if** — `POST /api/pricing/whatif` with
`{"product_id": "fans", "price_change_pct": 10, "horizon_days": 30}`

```json
{"product": "Fans", "current_price_inr": 1900.0, "new_price_inr": 2090.0,
 "elasticity": {"low": -0.4, "base": -0.7, "high": -1.2},
 "profit_change_inr": {"low": 21488.0, "base": 19004.0, "high": 14864.0},
 "breakeven_demand_drop_pct": 27.54,
 "sentence": "A 10% price rise for Fans keeps profit level if demand falls by no more than 27.54% (unit margin 500 to 690 rupees), assuming an elasticity of -0.7.",
 "assumptions": [{"id": "price_elasticity", "source": "assumed", "editable": true}]}
```

**Business + analytics** — `GET /api/business`

```json
{"name": "Sharma Hardware and Electricals", "cash": 50000,
 "analytics": {
   "dependency_shares": {"supplier_dependency": [
     {"supplier": "Supplier A", "supplier_id": "sup_a", "stock_value_share_pct": 87.7,
      "purchase_value_share_pct": 79.7, "concentration": "high"}]},
   "stock_cover": [{"product": "Fans", "stock_units": 36.0, "daily_demand": 4.0,
     "cover_days": 9.0, "next_restock_day": 8, "days_to_stockout": 9.0, "status": "watch"}],
   "attention_inputs": [{"kind": "supplier_concentration", "entity": "Supplier A",
     "severity": "warning", "day": null,
     "evidence": "Supplier A carries 79.7 percent of purchase value."}]}}
```

---

## 7. File structure

Generated from the real repository (excluding `node_modules`, `.next`, caches and
`__pycache__`).

```
valuehack/
├── README.md                     This file
├── generate_backend.py           Scaffolding scripts used to create the initial
├── generate_frontend.py          project files (not part of the running app)
├── generate_pages.py
├── backend/
│   ├── Makefile                  `make test` (pytest -q), `make run` (uvicorn)
│   ├── requirements.txt          Python dependencies (unpinned)
│   ├── .env.example              Template env file (GEMINI_API_KEY; see §9)
│   ├── bizsim.db                 SQLite demo database (committed; recreated on start)
│   ├── app/
│   │   ├── main.py               FastAPI app, CORS, error handler, all routes
│   │   ├── db.py                 SQLite engine + session
│   │   ├── models.py             SQLModel rows (Business, Supplier, Product, Customer)
│   │   ├── seed.py               DEMO_BUSINESS — the only place demo numbers live
│   │   ├── engine/
│   │   │   ├── models.py         Business/Product/Supplier/Customer/Shock models + schedule
│   │   │   ├── adapters.py       Build a Business from a dict or the database
│   │   │   ├── cascade.py        Shock → plan; resolve_target; simulate entry point
│   │   │   ├── sim.py            The day-by-day loop, events, timelines
│   │   │   ├── actions.py        Six actions, affordability, risk rubric, suggestion
│   │   │   ├── pricing.py        Price what-if, elasticity bands, curve, break-even
│   │   │   ├── analytics.py      Dependency shares, stock cover, attention inputs
│   │   │   ├── ranges.py         Low/base/high demand runs and range note
│   │   │   ├── errors.py         EngineError + error codes ({code, message})
│   │   │   ├── forecast.py       EMPTY (not implemented)
│   │   │   ├── anomaly.py        EMPTY (not implemented)
│   │   │   └── cash.py           EMPTY (not implemented)
│   │   ├── explain/
│   │   │   ├── reasons.py        Explanations, cascade chain, assumptions, format_inr
│   │   │   └── report.py         Hard-coded PDF (stub)
│   │   ├── routers/engine.py     POST /api/pricing/whatif (additive addition)
│   │   └── signals/
│   │       ├── llm.py            Regex scenario parser (no LLM)
│   │       ├── vendor.py         Mock vendor registry (name-based rule)
│   │       ├── bills.py          EMPTY (not implemented)
│   │       └── gstin.py          EMPTY (not implemented)
│   └── tests/
│       ├── conftest.py           Shared fixtures (demo business, engine entry points)
│       ├── test_oracle.py        The ten hand-calculated oracle rows
│       ├── test_headline.py      Demo headline numbers end to end
│       ├── test_golden.py        Legacy fields vs frozen golden JSON
│       ├── test_properties.py    Monotonicity properties (longer delay → no earlier stock-out)
│       ├── test_explanations.py  Every metric has an explanation with its own value
│       ├── test_validation.py    Invalid input → {code, message}
│       ├── test_pricing.py       Price what-if arithmetic and elasticity bounds
│       ├── test_analytics.py     Dependency shares and stock cover
│       ├── test_performance.py   Actions/price timings under the 300 ms budget
│       └── golden/               Frozen responses: business, baseline, delay14, actions
├── frontend/
│   ├── package.json              Next.js 14 app, deps in §8
│   ├── next.config.mjs           Note: eslint + typescript checks are skipped during build
│   ├── tailwind.config.ts        Design tokens (primary, success, warning, danger)
│   ├── .env.local.example        NEXT_PUBLIC_API_BASE_URL
│   ├── app/
│   │   ├── layout.tsx            Shell, fonts, background, TopNav
│   │   ├── page.tsx              Landing page
│   │   ├── fire-drill/page.tsx   Main screen: controls → cascade → charts → why → actions
│   │   ├── dashboard/page.tsx    KPIs, dependency bars, stock cover, attention
│   │   ├── pricing/page.tsx      Price what-if (slider reads the precomputed curve)
│   │   ├── report/page.tsx       Engine numbers + PDF download
│   │   ├── vendor-check/page.tsx Vendor trust check (mock) + Fire Drill deep link
│   │   ├── bill-scan/page.tsx    Upload → stub endpoint, labelled as stub
│   │   └── about/page.tsx        Model card and assumptions
│   ├── components/
│   │   ├── fire-drill/           ScenarioControls, CascadeMap, TimelinesChart,
│   │   │                         WhyPanel, AssumptionsBox, RangesPanel, ActionsCompare
│   │   ├── ui/                   states.tsx (loading/empty/error), badges.tsx
│   │   └── nav/TopNav.tsx        Navigation with a mobile-scrollable row
│   └── lib/
│       ├── api.ts                Typed client, ApiError ({code, message}), base URL
│       ├── types.ts              Types matching the API contract
│       └── format.ts             ₹ (Indian grouping), day/count/percent, colour tokens
└── docs/
    ├── api_contract_engine.md    Frozen engine shapes (Person 1 → 3/4)
    ├── engine_decisions.md       Eleven recorded decisions and their reasoning
    ├── engine_audit.md           Before/after audit of the engine layer
    ├── frontend_gap_list.md      What the backend returned vs what the UI showed
    ├── samples/                  Real, trimmed API responses + a capture script
    ├── screenshots/              demo-walkthrough.webm (see §3)
    ├── BizSim_Engineering_Report.md    Full engineering report
    ├── BizSim_Engineering_Report.pdf   The same report as a PDF (11 pages)
    └── md_to_pdf.py             Small ReportLab converter that builds that PDF
                              (pandoc is present but the LaTeX engine is missing packages)
```

---

## 8. Tech stack

Backend (`backend/requirements.txt` is **unpinned**; versions below are the
installed ones that produced the results in this README):

| Package | Installed version | Why |
|---|---|---|
| Python | 3.12.5 | Runtime |
| fastapi | 0.136.1 | HTTP API, validation, OpenAPI docs |
| uvicorn | 0.24.0 | ASGI server |
| pydantic | 2.13.3 | Request models, error serialisation |
| sqlmodel | 0.0.38 | SQLite rows for the seeded business |
| reportlab | 5.0.1 | PDF generation (`explain/report.py`) |
| pytest | 7.4.3 | Test runner (dev tool, not in requirements.txt) |
| pandas / numpy / scikit-learn / statsmodels / networkx | 2.2.3 / 1.26.4 / 1.6.1 / 0.15.0 / 3.7 | Present for the planned forecast/anomaly work; **not used by the running engine** |
| google-generativeai / pdf2image / Pillow / python-multipart | 0.8.6 / 1.17.0 / 10.4.0 / 0.0.27 | Installed for planned LLM bill scanning; only `python-multipart` is used (bill-scan upload) |

Frontend (`frontend/package.json`):

| Package | Version | Why |
|---|---|---|
| next | 14.2.35 | App Router UI |
| react / react-dom | ^18 | UI runtime |
| tailwindcss | ^3.4.1 | Styling and the design tokens |
| recharts | ^3.10.1 | Cash, stock and price-curve charts |
| @xyflow/react (React Flow) | ^12.12.0 | The six-step cascade map |
| framer-motion | ^13.5.0 | Staggered cascade reveal (reduced-motion respected) |
| lucide-react | ^1.49.0 | Icons |
| next-themes | ^0.4.6 | Present for theming; the app currently ships dark by default |
| typescript / eslint / eslint-config-next | ^5 / ^8 / 14.2.35 | Types and lint |

Node **v24.11.0**, npm **11.6.1**.

---

## 9. Setup and run

**Prerequisites:** Python 3.12+, Node 20+ (tested on 24), npm.

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
# or: make run   (uses --reload)
```

Serves `http://localhost:8000` (health: `GET /health` → `{"ok": true, "version": "1.0"}`,
docs at `/docs`). The database `backend/bizsim.db` is created on first start and
the demo business is seeded automatically on startup (`seed_demo_data()`).
`GET /api/business` falls back to the in-code `DEMO_BUSINESS` if the database
is unavailable, so the demo always works.

> Repo hygiene note: this repository currently **tracks** `backend/bizsim.db`
> and the generated `__pycache__` files, and had no `.gitignore`. A root
> `.gitignore` has now been added for new junk (logs, caches, `.env.local`,
> `node_modules`, `.next`, `bizsim.db`). The already-tracked generated files were
> deliberately **not** removed from the index, so teammates' work is unaffected.

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

If port 3000 is taken Next picks another port — check the line it prints.

### Environment variables actually read by the code

| Variable | Where read | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `frontend/lib/api.ts` | Backend base URL for all API calls |
| `NEXT_PUBLIC_API_URL` | `frontend/lib/api.ts` | Legacy fallback, used only if the above is unset |
| `GEMINI_API_KEY` | **not read by any running code** | Listed in `backend/.env.example` for the planned bill-scan/LLM work |

One variable, one place: `frontend/.env.local.example` and `backend/.env.example`
are the templates. Nothing else in the backend reads the environment.

### Tests

```bash
cd backend && pytest -q          # or: make test
cd frontend && npm run lint && npm run build && npx tsc --noEmit
```

> Note: `frontend/next.config.mjs` sets `typescript.ignoreBuildErrors` and
> `eslint.ignoreDuringBuilds`, so `npm run build` alone would not catch type
> errors. Run `npx tsc --noEmit` as well (documented above) — the current tree is
> clean.

### Reset the demo data

```bash
cd backend && rm bizsim.db && python -m uvicorn app.main:app --port 8000
```

The next start recreates and reseeds the database from `seed.py`.

---

## 10. Testing

Backend: 10 test modules, **50 tests**, in `backend/tests/`.

* **Oracle approach** — the reference table from the task brief was hand-
  calculated, and `test_oracle.py` reproduces all ten rows exactly (baseline;
  14-day delay; extension; discount only; extension + discount; switch to the new
  distributor, affordable and unaffordable; vendor vanishes; 15% and 30% cost
  spikes; late customer), with the arithmetic written into the test comments.
* **Headline** (`test_headline.py`) — the demo numbers quoted in §5.
* **Characterization** (`test_golden.py` + `tests/golden/*.json`) — the legacy
  response fields keep their names, types and values, so older screens keep
  working while new fields are added alongside.
* **Properties** (`test_properties.py`) — e.g. a longer supplier delay never
  produces an *earlier* stock-out.
* **Explanations** (`test_explanations.py`) — every `summary` metric has an
  explanation whose sentence contains that metric's own formatted value.
* **Validation** (`test_validation.py`) — invalid shock type and out-of-range
  elasticity return the `{code, message}` format.
* **Performance** (`test_performance.py`) — action comparison and price what-if
  stay inside the 300 ms budget.

Last real run on this branch: **50 passed, 20 warnings in 2.58s** (the warnings
are SQLModel `session.query()` deprecation notices). Exact numbers, timings and
the per-test table are in `docs/BizSim_Engineering_Report.md`.

Frontend: no automated UI test suite. `npm run lint`, `npm run build` and
`npx tsc --noEmit` pass, and the demo path was walked manually in a browser — the
executed checks are tabulated in the engineering report.

---

## 11. Data honesty

| Data | Status | Where |
|---|---|---|
| Demo business (stock, demand, prices, invoice dates, cash) | **Synthetic**, invented for the demo | `backend/app/seed.py` (`DEMO_BUSINESS`) |
| Vendor registry (scores, reasons) | **Mock** — a string rule, not a registry lookup | `backend/app/signals/vendor.py` |
| GSTIN checksum / registry, court or media data | **Not implemented** | `signals/gstin.py` is empty |
| Bill extraction | **Stub** — fixed sample response, no document parsing | `main.py`, `signals/bills.py` empty |
| Tax rate table | **Not implemented** — the stub returns a fixed 18% per item | `main.py` |
| Scenario parser (“plain words”) | **Mock** — regex, no LLM call | `signals/llm.py` |
| Explanations | **Generated by templates** from computed values (no LLM) | `explain/reasons.py` |
| Price elasticity (−0.4 / −0.7 / −1.2) | **Assumption**, returned with `source: "assumed"` | `engine/pricing.py` |
| Risk scores | **Heuristic** rubric, not probabilities | `engine/actions.py` |
| Report PDF | Real PDF, **hard-coded text** that ignores engine output | `explain/report.py` |
| Everything shown in the UI | **Synthetic demo data** — labelled in the UI header and on every estimate | UI + `seed.py` |

---

## 12. Limitations and roadmap

**Limitations (honest, current):**

* Estimates from one deterministic 30-day model, not forecasts. No external
  financing, no partial payments, demand held at recent averages (a demand band
  of ±20% is shown instead).
* The action comparison models the supplier-delay case only, because
  `POST /api/actions/compare` accepts a `delay` and nothing else; the UI says so
  when you pick another scenario type.
* The vendor hook is a stub, so `switch_supplier` always shows band `unknown`
  and no exposure; the demo vendor check is a mock.
* The report PDF ignores the engine (hard-coded text with a fixed
  recommendation that disagrees with the real suggestion).
* No forecast, anomaly detection, GSTIN checksum, CSV upload or bill parsing.
* `ranges` returns metric summaries only (no per-day low/high cash timelines), so
  the cash chart cannot shade a per-day demand band without the frontend
  computing business figures — it shows a min/base/max strip and the engine's
  `range_note` instead.
* Frontend build config skips type/lint checks, so `npx tsc --noEmit` and
  `npm run lint` must be run separately (both currently clean).
* No automated UI tests; verification was manual in a browser.

**Roadmap (prioritised):**

1. Regenerate `explain/report.py` from the live engine output (headline, cascade,
   suggested action, risk factors, assumptions) instead of fixed text.
2. Wire `get_vendor_risk()` to a real registry check so the `switch_supplier`
   card can show a band, exposure and the vendor-vanishes result on real data.
3. Make `/api/actions/compare` scenario-aware (accept the same `scenario` object
   as `/api/simulate/cascade`) so action comparison works for cost spikes and
   customer delays.
4. Return per-run cash/stock timelines in `ranges.runs[]` so the chart can shade
   the demand band.
5. Add CSV business loading with validation errors in the `{code, message}`
   format, plus the onboarding screen for it.
6. Implement real bill scanning (`signals/bills.py`) and the GSTIN checksum.
7. Add a Playwright smoke test for the demo path and capture screenshots in CI.
8. Turn on `typescript.ignoreBuildErrors` off and add type checking to the build.

---

## 13. Team and licence

| Role | Name |
|---|---|
| Person 1 — Engine, explanations, frontend, docs | *(add name)* |
| Person 2 — Attention list / signals | *(add name)* |
| Person 3 — Fire Drill UI | *(add name)* |
| Person 4 — Vendor module | *(add name)* |

**Licence:** *(add a licence — none has been chosen yet)*.

---

*BizSim gives estimates, not predictions. The tool suggests; the owner decides.*
