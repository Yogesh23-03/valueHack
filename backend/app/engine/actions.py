"""Preventive-action comparison.

Every action runs through the same simulator as a shock. Each result carries:

* the full simulation response (so the frontend keeps its existing fields),
* ``delta_vs_do_nothing`` and a plain-language ``tradeoff``,
* ``affordable`` / ``shortfall_inr`` for payments that exceed cash on their day,
* a transparent, tunable ``risk`` rubric (see ``docs/engine_decisions.md``),
* exactly one ``suggested`` action, or none with an honest note.

The legacy action ids (``do_nothing``, ``ask_extension``, ``early_discount``,
``switch_vendor``, ``combined``) keep working; ``switch_supplier`` adds the
working new-vendor case.
"""

from __future__ import annotations

from typing import Literal, Optional, TypedDict

from .cascade import to_response
from .models import Business, Plan, Shock
from .sim import simulate_plan


class VendorRisk(TypedDict):
    score: int  # 0..100
    band: Literal["green", "amber", "red", "unknown"]
    reasons: list[str]


def get_vendor_risk(vendor_identifier: str) -> VendorRisk:
    """Stub: returns band 'unknown'.

    Person 4 replaces the body by calling ``signals.vendor``. The signature is
    frozen for the API contract (see ``docs/api_contract_engine.md``).
    """
    return {"score": -1, "band": "unknown", "reasons": ["Vendor check not connected"]}


# ---------------------------------------------------------------------------
# Risk rubric
# ---------------------------------------------------------------------------

RISK_POINTS = {
    "cash_gap": 2,
    "failed_payable": 1,
    "unaffordable": 2,
    "counterparty": 1,
    "stockout": 1,
    "vendor_red": 3,
    "vendor_amber": 1,
    "vendor_unknown": 1,
}


def _risk_level(score: int) -> str:
    if score <= 1:
        return "Low"
    if score <= 3:
        return "Medium"
    return "High"


def _compute_risk(
    result,
    business,
    *,
    requires_counterparty: bool,
    affordable: bool,
    vendor_risk: Optional[VendorRisk],
) -> dict:
    factors: list[dict] = []
    score = 0

    if result.summary.get("first_negative_day") is not None:
        score += RISK_POINTS["cash_gap"]
        factors.append(
            {
                "points": RISK_POINTS["cash_gap"],
                "reason": f"Cash goes below zero on day {result.summary['first_negative_day']}.",
            }
        )
    fails = [e for e in result.events if e.type == "payable_failed"]
    if fails:
        score += RISK_POINTS["failed_payable"] * len(fails)
        factors.append(
            {
                "points": RISK_POINTS["failed_payable"] * len(fails),
                "reason": f"{len(fails)} supplier payment(s) cannot be made.",
            }
        )
    if not affordable:
        score += RISK_POINTS["unaffordable"]
        factors.append(
            {"points": RISK_POINTS["unaffordable"], "reason": "A required payment is not affordable on its day."}
        )
    if requires_counterparty:
        score += RISK_POINTS["counterparty"]
        factors.append(
            {"points": RISK_POINTS["counterparty"], "reason": "Needs a counterparty to agree."}
        )
    scope = result.details.get("scope_supplier")
    scoped_ids = {p.id for p in business.products if scope is None or p.supplier == scope}
    run_days = max(
        (
            int(v.get("days", 0))
            for pid, v in result.details.get("lost_sales_products", {}).items()
            if pid in scoped_ids
        ),
        default=0,
    )
    if run_days >= 5:
        score += RISK_POINTS["stockout"]
        factors.append(
            {
                "points": RISK_POINTS["stockout"],
                "reason": f"An unmitigated stock-out lasts {run_days} days.",
            }
        )
    if vendor_risk is not None:
        band = vendor_risk["band"]
        if band == "red":
            score += RISK_POINTS["vendor_red"]
            factors.append(
                {"points": RISK_POINTS["vendor_red"], "reason": "The new vendor is rated red."}
            )
        elif band == "amber":
            score += RISK_POINTS["vendor_amber"]
            factors.append(
                {"points": RISK_POINTS["vendor_amber"], "reason": "The new vendor is rated amber."}
            )
        elif band == "unknown":
            score += RISK_POINTS["vendor_unknown"]
            factors.append(
                {"points": RISK_POINTS["vendor_unknown"], "reason": "The vendor is not verified."}
            )

    return {"level": _risk_level(score), "score": score, "factors": factors}


# ---------------------------------------------------------------------------
# Action construction
# ---------------------------------------------------------------------------


def _advance_failure(result):
    for e in result.events:
        if e.type == "payable_failed" and e.values.get("kind") == "advance":
            return e
    return None


def compare_actions(
    delay: int,
    business: Optional[Business] = None,
    *,
    demand_band_pct: float = 20.0,
) -> dict:
    """Run and compare the standard set of actions for ``delay``.

    Returns a dict keyed by action id. The five legacy ids are preserved and
    ``switch_supplier`` is added for the working new-vendor case.
    """
    if business is None:
        from ..seed import demo_business_dict
        from .adapters import business_from_dict

        business = business_from_dict(demo_business_dict())

    primary = business.primary_supplier
    shock = Shock(type="supplier_delay", target=primary or "", magnitude=float(delay)) if delay else None
    first_customer = business.customers[0].id if business.customers else None
    payable_target = business.payables[0].supplier if business.payables else None
    from .ranges import compute_ranges

    def run(plan: Plan):
        result = simulate_plan(business, plan)
        result.ranges = compute_ranges(business, plan, demand_band_pct=demand_band_pct)
        return result

    base_plan = Plan(shock=shock, label="do_nothing")
    do_nothing = run(base_plan)
    base_summary = do_nothing.summary

    specs: list[dict] = []

    def spec(key: str, label: str, plan: Plan, *, counterparty=False, vendor_risk=None, vendor_fails=None):
        specs.append(
            {
                "key": key,
                "label": label,
                "plan": plan,
                "counterparty": counterparty,
                "vendor_risk": vendor_risk,
                "vendor_fails": vendor_fails,
            }
        )

    extension = Plan(
        shock=shock,
        invoice_extension_days=15,
        invoice_extension_supplier=primary,
        label="ask_extension",
    )
    discount = Plan(
        shock=shock,
        early_discount_pct=3.0,
        discount_customer=first_customer,
        label="early_discount",
    )
    combined = Plan(
        shock=shock,
        invoice_extension_days=15,
        invoice_extension_supplier=primary,
        early_discount_pct=3.0,
        discount_customer=first_customer,
        label="combined",
    )
    switch_vendor_id = business.alternative_vendor.name if business.alternative_vendor else "new vendor"
    vrisk = get_vendor_risk(switch_vendor_id)
    switch = Plan(shock=shock, switch_vendor=True, label="switch_supplier")
    switch_fails = Plan(shock=shock, switch_vendor=True, vendor_fails=True, label="switch_vendor_fails")

    supplier_label = business.supplier_name(primary) or "the supplier"
    customer_label = business.customer_name(first_customer) or "the customer"
    spec("do_nothing", "Do nothing", base_plan)
    spec("ask_extension", f"Ask {supplier_label} for an extension", extension, counterparty=True)
    spec("early_discount", f"Offer {customer_label} an early-payment discount", discount, counterparty=True)
    spec("switch_vendor", "Switch to the new distributor (vanishes)", switch_fails, vendor_risk=vrisk)
    spec("combined", "Extension plus discount", combined, counterparty=True)
    spec("switch_supplier", "Switch to the new distributor", switch, vendor_risk=vrisk, vendor_fails=switch_fails)

    results: dict[str, dict] = {}
    risk_by_key: dict[str, int] = {}
    no_gap: list[tuple[int, float, str]] = []

    vendor_fails_result = run(switch_fails)

    for s in specs:
        result = run(s["plan"])
        advance_fail = _advance_failure(result)
        affordable = advance_fail is None
        shortfall = float(advance_fail.values.get("shortfall_inr", 0)) if advance_fail else 0.0

        risk = _compute_risk(
            result,
            business,
            requires_counterparty=s["counterparty"],
            affordable=affordable,
            vendor_risk=s["vendor_risk"],
        )
        risk_by_key[s["key"]] = risk["score"]

        response = to_response(result)
        response.update(
            {
                "id": s["key"],
                "label": s["label"],
                "delta_vs_do_nothing": _delta(base_summary, result.summary),
                "tradeoff": _tradeoff(business, s, result, base_summary, affordable, shortfall),
                "affordable": affordable,
                "shortfall_inr": round(shortfall, 2),
                "requires_counterparty_agreement": bool(s["counterparty"]),
                "risk": risk,
                "suggested": False,
                "vendor_risk": s["vendor_risk"],
                "exposure_inr": (
                    round(max(0.0, _advance_amount(result)), 2) if s["vendor_risk"] and s["vendor_risk"]["band"] == "red" else None
                ),
                "vendor_fails_result": (
                    to_response(vendor_fails_result) if s["key"] == "switch_supplier" else None
                ),
            }
        )
        results[s["key"]] = response

        if result.summary.get("first_negative_day") is None:
            no_gap.append((risk["score"], float(result.summary.get("end_cash_inr", 0.0)), s["key"]))

    # --- suggested action --------------------------------------------------
    suggested_key: Optional[str] = None
    if no_gap:
        no_gap.sort(key=lambda t: (t[0], -t[1], t[2]))
        suggested_key = no_gap[0][2]
        reason = (
            f"Suggested: {results[suggested_key]['label']}. It avoids the cash gap with the lowest "
            f"risk score ({risk_by_key[suggested_key]}) and the highest end cash among those options."
        )
    else:
        reason = "No action avoids the cash gap, so none is marked suggested. The estimates are not a promise."

    for key, response in results.items():
        response["suggested"] = key == suggested_key
        response["suggested_reason"] = reason

    return results


def _advance_amount(result) -> float:
    for e in result.events:
        if e.type == "payable_failed" and e.values.get("kind") == "advance":
            return float(e.values.get("amount_inr", 0.0))
    # If the advance was affordable, read it from the payable_paid event.
    for e in result.events:
        if e.type == "payable_paid" and "advance" in e.entity.lower():
            return float(e.values.get("amount_inr", 0.0))
    return 0.0


def _delta(base: dict, new: dict) -> dict:
    keys = [
        "stockout_day",
        "lost_sales_inr",
        "first_negative_day",
        "lowest_cash_inr",
        "end_cash_inr",
        "failed_payments_count",
    ]
    out: dict = {}
    for k in keys:
        b = base.get(k)
        n = new.get(k)
        out[k] = {"base": b, "action": n, "delta": (None if b is None or n is None else round(n - b, 2))}
    return out


def _tradeoff(business, spec, result, base_summary, affordable, shortfall) -> str:
    parts: list[str] = []
    base_gap = base_summary.get("first_negative_day")
    action_gap = result.summary.get("first_negative_day")
    if base_gap is not None and action_gap is None:
        parts.append("Avoids the cash gap")
    elif action_gap is not None:
        parts.append(f"Still leaves cash below zero on day {action_gap}")
    else:
        parts.append("Keeps cash positive")

    base_lost = base_summary.get("lost_sales_inr", 0) or 0
    action_lost = result.summary.get("lost_sales_inr", 0) or 0
    if action_lost < base_lost:
        parts.append(f"cuts lost sales by {_inr(base_lost - action_lost)}")
    elif action_lost > base_lost:
        parts.append(f"increases lost sales by {_inr(action_lost - base_lost)}")
    else:
        parts.append("does not change the stock-out")

    if not affordable:
        parts.append(f"but needs {_inr(shortfall)} more cash than is available on the payment day")

    cash_delta = (result.summary.get("end_cash_inr", 0) or 0) - (base_summary.get("end_cash_inr", 0) or 0)
    if cash_delta < 0:
        parts.append(f"and lowers end cash by {_inr(-cash_delta)}")
    elif cash_delta > 0:
        parts.append(f"and raises end cash by {_inr(cash_delta)}")

    if spec["counterparty"]:
        parts.append("and needs the counterparty to agree")

    return ". ".join(parts) + "."


def _inr(v: float) -> str:
    from ..explain.reasons import format_inr

    return format_inr(v)
