"""Backward-compatible entry point for the cascade simulation.

``simulate`` keeps the original keyword arguments and response fields the
frontend already uses, and adds the richer engine fields (``summary``,
``cascade_chain``, ``events``, ``explanations``, ``assumptions``, ``ranges``,
``meta``) alongside them. It builds the demo business from seed data and never
hard-codes demo numbers itself.
"""

from __future__ import annotations

from typing import Any, Optional

from ..seed import demo_business_dict
from .adapters import business_from_dict
from .models import Business, Plan, Shock
from .sim import simulate_plan

DEFAULT_DEMAND_BAND_PCT = 20.0


def build_plan(
    business: Business,
    *,
    delay: int = 0,
    ext_a: int = 0,
    ext_c: int = 0,
    early_discount: float = 0.0,
    alt_supplier: bool = False,
    alt_fails: bool = False,
    cost_spike_pct: float = 0.0,
    customer_late_days: int = 0,
    shock: Optional[Shock] = None,
) -> Plan:
    """Translate the legacy keyword arguments into a :class:`Plan`.

    An explicit ``shock`` (from the scenario dispatcher) takes precedence over
    the legacy ``delay``/``cost_spike_pct``/``customer_late_days`` fields.
    """
    primary = business.primary_supplier
    if shock is None:
        if delay:
            shock = Shock(type="supplier_delay", target=primary or "", magnitude=float(delay))
        elif cost_spike_pct:
            shock = Shock(type="cost_spike", target=primary or "", magnitude=float(cost_spike_pct))
        elif customer_late_days:
            customer = business.customers[0].id if business.customers else ""
            shock = Shock(type="customer_delay", target=customer, magnitude=float(customer_late_days))

    payable_target = None
    if ext_c and business.payables:
        payable_target = business.payables[0].supplier

    return Plan(
        shock=shock,
        invoice_extension_days=int(ext_a),
        invoice_extension_supplier=primary,
        payable_extension_days=int(ext_c),
        payable_extension_target=payable_target,
        early_discount_pct=float(early_discount) * 100.0,
        discount_customer=(business.customers[0].id if business.customers else None) if early_discount else None,
        switch_vendor=bool(alt_supplier),
        vendor_fails=bool(alt_fails),
        label="legacy",
    )


def resolve_target(business: Business, shock: Optional[Shock]) -> Optional[Shock]:
    """Map a loose scenario target ('A', 'Supplier A') onto a real entity id."""
    if shock is None or not shock.target:
        return shock
    t = shock.target.strip().lower()

    def match(entities):
        for e in entities:
            if e.id.lower() == t or e.name.lower() == t:
                return e.id
        for e in entities:
            if e.id.lower().endswith(t) or e.name.lower().endswith(" " + t):
                return e.id
        return None

    if shock.type in ("supplier_delay", "cost_spike"):
        found = match(business.suppliers)
        return shock.model_copy(update={"target": found}) if found else shock
    if shock.type == "customer_delay":
        found = match(business.customers)
        return shock.model_copy(update={"target": found}) if found else shock
    return shock


def simulate(
    delay: int = 0,
    horizon: int = 30,
    start_cash: Optional[float] = None,
    ext_a: int = 0,
    ext_c: int = 0,
    early_discount: float = 0.0,
    alt_supplier: bool = False,
    alt_fails: bool = False,
    cost_spike_pct: float = 0.0,
    customer_late_days: int = 0,
    demand_band_pct: float = DEFAULT_DEMAND_BAND_PCT,
    business: Optional[Business] = None,
    plan: Optional[Plan] = None,
) -> dict[str, Any]:
    """Run the demo simulation and return the legacy + new response dict."""
    if business is None:
        business = business_from_dict(demo_business_dict())
    if horizon:
        business = business.model_copy(update={"horizon_days": int(horizon)})
    if start_cash is not None:
        business = business.model_copy(update={"cash_inr": float(start_cash)})

    if plan is None:
        plan = build_plan(
            business,
            delay=delay,
            ext_a=ext_a,
            ext_c=ext_c,
            early_discount=early_discount,
            alt_supplier=alt_supplier,
            alt_fails=alt_fails,
            cost_spike_pct=cost_spike_pct,
            customer_late_days=customer_late_days,
        )

    result = simulate_plan(business, plan, with_ranges=True)
    if demand_band_pct != DEFAULT_DEMAND_BAND_PCT:
        from .ranges import compute_ranges

        result.ranges = compute_ranges(business, plan, demand_band_pct=demand_band_pct)

    return to_response(result)


def to_response(result) -> dict[str, Any]:
    """Merge legacy fields with the new structured engine fields."""
    summary = result.summary
    delivered = any(
        rec.get("delivered_day") is not None for rec in result.details.get("delivered_orders", [])
    )
    legacy = {
        "stockout": summary.get("stockout_day"),
        "lost_rev": summary.get("lost_sales_inr"),
        "first_negative_day": summary.get("first_negative_day"),
        "min_cash": summary.get("lowest_cash_inr"),
        "min_day": summary.get("lowest_cash_day"),
        "failed": result.details.get("failed_payments", []),
        "delivered": delivered,
        "end_cash": summary.get("end_cash_inr"),
        "cash_timeline": result.timeline.get("cash", []),
        "stock_timeline": result.timeline.get("stock", []),
    }
    new = {
        "scenario": result.scenario,
        "summary": summary,
        "cascade_chain": [s.model_dump() for s in result.cascade_chain],
        "events": [e.model_dump() for e in result.events],
        "timeline": result.timeline,
        "explanations": [e.model_dump() for e in result.explanations],
        "assumptions": [a.model_dump() for a in result.assumptions],
        "ranges": result.ranges.model_dump(),
        "meta": result.meta,
    }
    return {**legacy, **new}
