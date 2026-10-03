# Frontend gap list (Phase A discovery)

What the backend now returns vs what the frontend shows. Written after reading
every frontend page, `docs/api_contract_engine.md`, and capturing live responses
in `docs/samples/` (all values below were seen in real API output, never
invented). Items marked **[B#]** are fixed in Phase B of the follow-up prompt;
status at the bottom of each line.

## Global / foundations

| # | Gap |
|---|-----|
| G1 | No TypeScript types for any API response; `lib/api.ts` returns `unknown` and pages re-declare ad-hoc interfaces. **[B1]** — done |
| G2 | Base URL is `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`); prompt asks to centralise as `NEXT_PUBLIC_API_BASE_URL`. **[B1]** — done: `NEXT_PUBLIC_API_BASE_URL` preferred, `NEXT_PUBLIC_API_URL` kept as fallback; `.env.local.example` added |
| G3 | Backend error format `{code, message}` (422/404, codes `INVALID_SHOCK`, `UNKNOWN_SUPPLIER`, `UNKNOWN_CUSTOMER`, `UNKNOWN_PRODUCT`, `MAGNITUDE_OUT_OF_RANGE`, `ELASTICITY_OUT_OF_RANGE`, `INVALID_INPUT`) is never surfaced; every page does `catch(e){console.error}` and shows nothing. **[B1]** — done: shared `ApiError` + friendly `ErrorState` with Retry and offline hint |
| G4 | No Indian-grouping rupee formatter (pages use `toLocaleString()`, which gives `₹171,600`, not `₹1,71,600`; negatives shown as `-₹…`). **[B1]** — done: `formatInr` in `lib/format.ts` (`₹-1,71,600` style) |
| G5 | No `Estimate` badge, no risk colour tokens with text (Low/Medium/High), no safe/watch/critical chips, no assumption `source` tags. **[B1]** — done: `components/ui/badges.tsx` |
| G6 | No reusable loading skeleton / empty / error states; dashboard shows plain text, fire-drill shows nothing. **[B1]** — done: `components/ui/states.tsx` |
| G7 | No `POST /api/pricing/whatif` anywhere in the client — the endpoint (curve, break-even, elasticity bands) is unreachable from the UI. **[B1/B5]** — done: new `/pricing` page |
| G8 | `GET /api/report` PDF is wired in `lib/api.ts` (`getReport`) but never called; the Report screen is a static print view. **[B4-adjacent]** — done: Download button + real numbers |
| G9 | TopNav hides all links below `md` — on a 360px phone there is no navigation at all. **[B6]** — done: horizontally scrollable nav row on mobile |

## Fire Drill (`app/fire-drill/page.tsx`)

| # | Gap |
|---|-----|
| F1 | Only a supplier-delay slider exists. Scenario types `customer_delay` and `cost_spike` (and `demand_shock`), `target`, per-type magnitude are not controllable, although `POST /api/simulate/cascade` accepts `scenario:{type,target,magnitude,duration_days}` plus `customer_late_days` / `cost_spike_pct`. **[B2]** — done |
| F2 | The plain-language box that calls `POST /api/scenario/parse` does not exist in the UI (endpoint works: `{"type":"supplier_delay","target":"A","days":14}`). **[B2]** — done |
| F3 | `demand_band_pct` (0–50) is never sent; `ranges` in the response therefore always reflect the default ±20%. **[B2]** — done: slider sends it; runs recompute |
| F4 | Cascade "map" is 5 hard-coded flex chips (Supplier A/Stock/Orders/Cash/Payables) with labels invented in the UI. The API returns the real 6-step `cascade_chain` (`supplier_delay → inventory_shortage → delayed_orders → customer_payment_delay → cash_gap → failed_supplier_payment`) with `status` (`triggered/avoided/not_reached`), `day`, `title`, `detail`. React Flow (`@xyflow/react`) is in `package.json` but unused. **[B2]** — done: React Flow map from `cascade_chain` |
| F5 | The chart's "Baseline" line is fabricated in the frontend: `50000 - i*3000`. Business figures must come from the API. Baseline exists in `/api/actions/compare` as `do_nothing.cash_timeline`. **[B2]** — done: baseline from `do_nothing` |
| F6 | "After Action" always plots `combined`, while the engine's `suggested` for a 14-day delay is `ask_extension` (the old "✓ BEST" badge on `combined` is also hard-coded and wrong). **[B2/B3]** — done: chart follows the `suggested` action; badge from `suggested` |
| F7 | `summary` (stock-out day, lost sales, first negative day, lowest cash, end cash, failed payments count, order delay, customer payment day) is not displayed anywhere. **[B2]** — done: headline strip |
| F8 | `explanations` (plain sentences per metric) — the "Why?" panel does not exist. **[B2]** — done |
| F9 | `events` (structured, with ids/days/severity/cause links) are not shown; no dated timeline. **[B2]** — done |
| F10 | `assumptions` (with `source: demo_data/assumed/user`, `editable`) are not shown. **[B2]** — done: always-visible box |
| F11 | `ranges` (min/base/max per metric, `range_note`) are not shown. Per-day low/high **cash timelines are not in the API** (`ranges.runs[]` holds metrics only), so a shaded per-day band cannot be drawn without the frontend computing business figures — shown as a min/base/max strip + `range_note` instead. **[B2]** — done (strip), band pending backend data |
| F12 | Stock per product (`stock_timeline`) is not charted. **[B2]** — done: stock lines per product |
| F13 | Failed payments (`failed[{name,day}]`) have no markers on the chart. **[B2]** — done: `ReferenceDot` markers |
| F14 | No auto-run on control change (must click Run), no debounce, no cancellation of stale requests. **[B2]** — done: 300 ms debounce + `AbortController` |
| F15 | No loading/empty/error states around the simulation call. **[B1/B2]** — done |

## Action comparison

| # | Gap |
|---|-----|
| A1 | Cards show only `min_cash` and `failed.length`; `stockout_day`, `lowest_cash`, `end_cash`, `delta_vs_do_nothing`, `tradeoff`, `risk` (+ expandable `factors`), `affordable`/`shortfall_inr`, `requires_counterparty_agreement` are all returned and all ignored. **[B3]** — done |
| A2 | `suggested` / `suggested_reason` from the engine are ignored; UI hard-codes "✓ BEST" on `combined`. **[B3]** — done |
| A3 | `switch_supplier` extras ignored: `vendor_risk` (band/score/reasons), `exposure_inr`, `vendor_fails_result`. No link to the vendor-check screen. **[B3]** — done |
| A4 | Note recorded: `POST /api/actions/compare` takes only `{delay}` — it is scenario-aware for the Supplier-A delay case; demand band does not affect it. UI labels the comparison accordingly (honest limitation, listed in the report). |
| A5 | No loading/error state for the actions call. **[B3]** — done |

## Dashboard (`app/dashboard/page.tsx`)

| # | Gap |
|---|-----|
| D1 | Three of four KPI numbers are hard-coded in the UI ("12 days", "₹70,000", "75%") — violates "numbers come from the API". **[B4]** — done: KPIs derive from `/api/business` |
| D2 | The supplier-concentration bar chart is hard-coded (A 75 / B 15 / C 10). The API returns real `analytics.dependency_shares.supplier_dependency` (Supplier A: 87.7% stock-value share, 79.7% purchase-value share, concentration `high`). **[B4]** — done |
| D3 | `analytics.stock_cover` (per product `cover_days`, `days_to_stockout`, `status: safe/watch/critical`, `next_restock_day`) is not shown. **[B4]** — done |
| D4 | `analytics.attention_inputs` (with `evidence`, `severity`, `entity`) are not shown; the `/api/attention` items render but the "Why?" button does nothing. **[B4]** — done: `/api/attention` items link to screens; engine `attention_inputs` rendered with evidence (both labelled honestly) |
| D5 | `/api/attention` is a hard-coded stub in the backend (Person 2 scope) — UI labels it "demo reminders". Not a frontend fix. |
| D6 | No loading skeleton / error / retry / offline state; no empty state. **[B1/B4]** — done |
| D7 | No demo-business loader/onboarding note: there is **no** `/api/business/load` or CSV upload endpoint in the backend, so none is faked (recorded in report as pending). |

## Price what-if (new page)

| # | Gap |
|---|-----|
| P1 | Page does not exist. Endpoint returns product, current/new price, elasticity bands (low −0.4 / base −0.7 / high −1.2), demand multipliers, profit low/base/high, break-even demand drop, a precomputed 21-point `curve` (−20…+20), a sentence, and assumptions (elasticity labelled `assumed`). **[B5]** — done: `/pricing` with product picker, slider reading `curve` (no refetch on slider move), elasticity control (refetch on change), low/base/high profit, break-even + sentence, Estimate + assumption labels |

## Other screens

| # | Gap |
|---|-----|
| O1 | Report page prints fabricated figures ("Combined approach … minimum cash ₹12,000") that contradict the engine (suggested action for the 14-day delay is `ask_extension`; combined leaves cash at ₹62,550 with no gap — different numbers). **[B4-adjacent]** — done: renders engine `suggested` + real summary from `/api/actions/compare`, Download PDF wired to `GET /api/report` |
| O2 | Vendor check works against the mock registry, but "Use this vendor in a Fire Drill" is a dead button. **[B3-adjacent]** — done: links to `/fire-drill?target=…` which prefills the target field |
| O3 | Bill scan page is fully static; `POST /api/bill/scan` is a backend stub returning a fixed sample (no file parsing, no sample bill files exist in the repo). **[B-adjacent]** — done: upload wired to the real endpoint, response labelled "demo stub output"; the honest limitation is kept visible |
| O4 | About page lists stale engine modules ("5 pre-defined strategies" — now 6; missing `engine/models.py`, `adapters`, `analytics`, `ranges`, `pricing`, `explain/reasons.py`; scenario parser described as regex — correct, `signals/llm.py` is a regex stub, no LLM call exists). **[B6]** — done: module list matches the tree |
| O5 | Charts/cascade have no aria labels; risk/danger signalled by colour alone in places. **[B6]** — done: labels + text alongside colour |
| O6 | No `.env.local.example`. **[B1]** — done |

## Verified working already (no change needed)

- Vendor check screen renders `{score, badge, reasons}` correctly for mock data.
- Scenario parse endpoint contract `{type, target, days}` matches the UI flow we add.
- Golden/legacy fields (`stockout`, `lost_rev`, `first_negative_day`, `min_cash`, `min_day`, `failed`, `delivered`, `end_cash`, `cash_timeline`, `stock_timeline`) are what the current screens read — all preserved by the engine, so nothing breaks while we extend.
