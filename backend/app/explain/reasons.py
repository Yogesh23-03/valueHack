"""Plain-language explanations for engine output.

Everything here is built from **computed values only**. Sentences are f-strings
and templates filled with numbers and names the engine produced; no language
model is involved, so no number can be invented, rounded or altered here.

``format_inr`` renders rupees with Indian digit grouping (for example
``₹1,77,600`` and ``₹-1,71,600``).
"""

from __future__ import annotations

from typing import Optional

from ..engine.models import (
    Assumption,
    Business,
    CascadeStep,
    Event,
    Explanation,
    Plan,
)

INR = "inr"
DAY = "day"
COUNT = "count"


# ---------------------------------------------------------------------------
# Money formatting
# ---------------------------------------------------------------------------


def format_inr(value: float | int) -> str:
    """Format a number as rupees with Indian digit grouping.

    ``0 -> ₹0``, ``1000 -> ₹1,000``, ``100000 -> ₹1,00,000``,
    ``177600 -> ₹1,77,600`` and ``-171600 -> ₹-1,71,600``.
    """
    amount = int(round(float(value)))
    negative = amount < 0
    digits = str(abs(amount))
    if len(digits) <= 3:
        body = digits
    else:
        head, tail = digits[:-3], digits[-3:]
        groups: list[str] = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        groups.insert(0, head)
        body = ",".join(groups) + "," + tail
    return ("₹-" if negative else "₹") + body


def display_value(unit: str, value: float | int | None) -> Optional[str]:
    """The exact string an explanation sentence must contain, or ``None``."""
    if value is None:
        return None
    if unit == INR:
        return format_inr(value)
    if unit == DAY:
        return str(int(value))
    if unit == COUNT:
        return str(int(value))
    return str(value)


# ---------------------------------------------------------------------------
# Small lookups over events
# ---------------------------------------------------------------------------


def _by_type(events: list[Event], type_: str) -> list[Event]:
    return [e for e in events if e.type == type_]


def _first(events: list[Event], type_: str) -> Optional[Event]:
    for e in events:
        if e.type == type_:
            return e
    return None


def _scoped_products(business: Business, details: dict) -> list[str]:
    scope = details.get("scope_supplier")
    if scope is None:
        return [p.id for p in business.products]
    return [p.id for p in business.products if p.supplier == scope]


def _product_name(business: Business, pid: str) -> str:
    for p in business.products:
        if p.id == pid:
            return p.name
    return pid


# ---------------------------------------------------------------------------
# Explanations
# ---------------------------------------------------------------------------


def build_explanations(
    business: Business,
    plan: Plan,
    summary: dict,
    events: list[Event],
    details: dict,
) -> list[Explanation]:
    """Return one explanation for every key in ``summary``."""
    exps: list[Explanation] = []

    def add(metric_id: str, label: str, unit: str, sentence: str, event_ids: Optional[list[str]] = None):
        exps.append(
            Explanation(
                metric_id=metric_id,
                label=label,
                value=summary.get(metric_id),
                unit=unit,
                sentence=sentence,
                event_ids=event_ids or [],
            )
        )

    horizon = business.horizon_days

    # --- stockout_day ------------------------------------------------------
    scoped_ids = set(_scoped_products(business, details))
    stockout_evs = [
        e for e in _by_type(events, "stockout_started") if e.values.get("product_id") in scoped_ids
    ]
    slipped = _first(events, "restock_slipped")
    if summary.get("stockout_day") is not None and stockout_evs:
        names = [e.entity for e in stockout_evs]
        name_txt = _join_names(names)
        day = summary["stockout_day"]
        if slipped is not None:
            sched = int(slipped.values.get("scheduled_day", slipped.day))
            actual = int(slipped.values.get("actual_day", slipped.day))
            sentence = (
                f"{name_txt} run out on day {day} because {slipped.entity}'s restock "
                f"slips from day {sched} to day {actual}."
            )
        else:
            sentence = f"{name_txt} run out on day {day}."
        add("stockout_day", "First stock-out day", DAY, sentence, [e.id for e in stockout_evs])
    else:
        add(
            "stockout_day",
            "First stock-out day",
            DAY,
            f"No product runs out within the {horizon}-day horizon.",
        )

    # --- lost_sales_inr (scoped to the disrupted supply chain) -------------
    scoped = set(_scoped_products(business, details))
    lost_evs = _by_type(events, "sales_lost")
    scoped_lost = [e for e in lost_evs if e.values.get("product_id") in scoped]
    if scoped_lost:
        names = [e.entity for e in scoped_lost]
        total_days = max(int(e.values.get("days", 1)) for e in scoped_lost)
        sentence = (
            f"Walk-in sales of {_join_names(names, lower=True)} stop for {total_days} days, "
            f"which loses about {format_inr(summary['lost_sales_inr'])} in sales."
        )
        add("lost_sales_inr", "Lost walk-in sales", INR, sentence, [e.id for e in scoped_lost])
    else:
        add(
            "lost_sales_inr",
            "Lost walk-in sales",
            INR,
            f"Walk-in sales of {_scope_name(business, details)} never stop, so no sales are lost.",
        )

    # --- lost_sales_all_products_inr --------------------------------------
    add(
        "lost_sales_all_products_inr",
        "Lost walk-in sales (all products)",
        INR,
        f"All products together lose about {format_inr(summary['lost_sales_all_products_inr'])} of walk-in sales.",
        [e.id for e in lost_evs],
    )

    # --- first_negative_day / lowest cash ---------------------------------
    failure_evs = _by_type(events, "payable_failed")
    if summary.get("first_negative_day") is not None:
        day = summary["first_negative_day"]
        same_day = [e for e in failure_evs if e.day == day]
        if same_day:
            ev = max(same_day, key=lambda e: float(e.values.get("amount_inr", 0)))
            amt = float(ev.values.get("amount_inr", 0))
            available = float(ev.values.get("available_inr", 0))
            shortfall = float(ev.values.get("shortfall_inr", 0))
            sentence = (
                f"Cash falls below zero on day {day}, when the {format_inr(amt)} {ev.entity} falls due "
                f"and only {format_inr(available)} is available, a shortfall of {format_inr(shortfall)}."
            )
            add("first_negative_day", "First day cash is below zero", DAY, sentence, [ev.id])
        else:
            neg_ev = _first(events, "cash_negative")
            add(
                "first_negative_day",
                "First day cash is below zero",
                DAY,
                f"Cash falls below zero on day {day} after the day's costs and payments.",
                [neg_ev.id] if neg_ev else [],
            )
    else:
        add(
            "first_negative_day",
            "First day cash is below zero",
            DAY,
            f"Cash never falls below zero within the {horizon}-day horizon.",
        )

    add(
        "lowest_cash_inr",
        "Lowest cash",
        INR,
        f"The lowest cash is {format_inr(summary['lowest_cash_inr'])} on day {summary['lowest_cash_day']}.",
    )
    add(
        "lowest_cash_day",
        "Day of lowest cash",
        DAY,
        f"The lowest cash lands on day {summary['lowest_cash_day']}.",
    )
    add(
        "end_cash_inr",
        "Cash at the end of the horizon",
        INR,
        f"Cash ends the {horizon}-day horizon at {format_inr(summary['end_cash_inr'])}.",
    )

    # --- failed payments ---------------------------------------------------
    count = int(summary.get("failed_payments_count", 0))
    if count:
        short = [f"the {format_inr(e.values.get('amount_inr', 0))} payment to {_short_name(e.entity)} on day {e.day}"
                 for e in failure_evs]
        if count == 1:
            sentence = f"1 supplier payment fails: " + short[0] + " cannot be made."
        else:
            sentence = f"{count} supplier payments fail: " + "; ".join(short) + "."
        add(
            "failed_payments_count",
            "Failed supplier payments",
            COUNT,
            sentence,
            [e.id for e in failure_evs],
        )
    else:
        add(
            "failed_payments_count",
            "Failed supplier payments",
            COUNT,
            "0 supplier payments fail; every amount due is paid on time.",
        )

    # --- order delay -------------------------------------------------------
    detail = _delayed_order_detail(business, details)
    if summary.get("order_delay_days") is not None and detail is not None:
        sentence = (
            f"{_possessive(detail['customer'])} order is delivered on day {detail['delivered_day']} instead of "
            f"day {detail['target_day']}, {summary['order_delay_days']} days late, so their payment moves from "
            f"day {detail['normal_pay_day']} to day {detail['actual_pay_day']}."
        )
        add("order_delay_days", "Order delay", DAY, sentence)
    else:
        add(
            "order_delay_days",
            "Order delay",
            DAY,
            "Every customer order is delivered on its target day.",
        )

    # --- customer payment day ---------------------------------------------
    if summary.get("customer_payment_day") is not None:
        add(
            "customer_payment_day",
            "Customer payment day",
            DAY,
            f"The customer pays on day {summary['customer_payment_day']}.",
        )
    else:
        add(
            "customer_payment_day",
            "Customer payment day",
            DAY,
            f"No customer payment arrives inside the {horizon}-day horizon.",
        )

    return exps


def _delayed_order_detail(business: Business, details: dict) -> Optional[dict]:
    for rec in details.get("delivered_orders", []):
        if rec.get("delivered_day") is None:
            continue
        order = next((o for o in business.orders if o.id == rec["order_id"]), None)
        if order is None:
            continue
        if rec["delivered_day"] > order.target_delivery_day:
            return {
                "customer": business.customer_name(order.customer) or order.customer,
                "target_day": order.target_delivery_day,
                "delivered_day": rec["delivered_day"],
                "normal_pay_day": order.target_delivery_day + order.payment_terms_days,
                "actual_pay_day": rec.get("pay_day"),
            }
    return None


def _short_name(entity: str) -> str:
    return entity.replace(" invoice", "").replace(" payable", "")


def _possessive(name: str) -> str:
    return name + "'" if name.endswith("s") else name + "'s"


def _scope_name(business: Business, details: dict) -> str:
    scoped = [_product_name(business, pid) for pid in _scoped_products(business, details)]
    return _join_names(scoped, lower=True) if scoped else "the disrupted products"


def _join_names(names: list[str], lower: bool = False) -> str:
    cleaned: list[str] = []
    for n in names:
        if n not in cleaned:
            cleaned.append(n)
    if lower:
        cleaned = [n[0].lower() + n[1:] if n else n for n in cleaned]
    if not cleaned:
        return "the products"
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f" and {cleaned[-1]}"


# ---------------------------------------------------------------------------
# Cascade chain
# ---------------------------------------------------------------------------

_ORDER = [
    ("supplier_delay", "Supplier delay"),
    ("inventory_shortage", "Inventory shortage"),
    ("delayed_orders", "Delayed orders"),
    ("customer_payment_delay", "Customer payment delay"),
    ("cash_gap", "Cash-flow gap"),
    ("failed_supplier_payment", "Failed supplier payment"),
]


def build_cascade_chain(
    business: Business,
    plan: Plan,
    summary: dict,
    events: list[Event],
    details: dict,
) -> list[CascadeStep]:
    """Return the six cascade steps in their fixed order."""
    slipped = _first(events, "restock_slipped")
    scoped_ids = set(_scoped_products(business, details))
    stockout = next(
        (e for e in events if e.type == "stockout_started" and e.values.get("product_id") in scoped_ids),
        None,
    )
    delayed = _first(events, "order_delayed")
    pushed = _first(events, "receivable_pushed")
    negative = _first(events, "cash_negative")
    failures = _by_type(events, "payable_failed")
    # The cascade's final step is the *cascaded* failure (the payment that fails
    # because cash is already negative), so we report the last failure day.
    last_failure = failures[-1] if failures else None

    triggered_flags = [
        slipped is not None,
        stockout is not None,
        delayed is not None,
        pushed is not None,
        negative is not None,
        bool(failures),
    ]
    days = [
        slipped.day if slipped else None,
        stockout.day if stockout else None,
        delayed.day if delayed else None,
        pushed.day if pushed else None,
        negative.day if negative else None,
        last_failure.day if last_failure else None,
    ]
    details_txt = [
        (
            f"{slipped.entity}'s restock slips from day {int(slipped.values.get('scheduled_day', slipped.day))} "
            f"to day {int(slipped.values.get('actual_day', slipped.day))}."
            if slipped
            else "No supplier delivery is late."
        ),
        (
            f"Stock runs out on day {stockout.day}; walk-in demand cannot be fully served."
            if stockout
            else "Stock covers demand through the horizon."
        ),
        (
            f"{delayed.entity}'s order is delivered on day {delayed.day}, "
            f"{int(delayed.values.get('days_late', 0))} days late."
            if delayed
            else "Every order is delivered on its target day."
        ),
        (
            f"{pushed.entity} pays on day {pushed.day} instead of day {int(pushed.values.get('normal_day', pushed.day))}."
            if pushed
            else "Customer payment terms are met."
        ),
        (
            f"Cash falls below zero on day {negative.day}."
            if negative
            else "Cash stays positive through the horizon."
        ),
        (
            f"{len(failures)} supplier payment(s) fail, the last on day {last_failure.day}."
            if last_failure
            else "Every supplier payment is made."
        ),
    ]

    chain: list[CascadeStep] = []
    for i, (step, title) in enumerate(_ORDER):
        if triggered_flags[i]:
            status = "triggered"
        elif any(triggered_flags[:i]):
            status = "avoided"
        else:
            status = "not_reached"
        chain.append(
            CascadeStep(
                step=step,
                status=status,  # type: ignore[arg-type]
                day=days[i],
                title=title,
                detail=details_txt[i],
            )
        )
    return chain


# ---------------------------------------------------------------------------
# Assumptions
# ---------------------------------------------------------------------------


def build_assumptions(business: Business, plan: Plan) -> list[Assumption]:
    """Return the modelling assumptions behind a run. Never empty."""
    assumptions: list[Assumption] = []

    for r in business.restocks:
        assumptions.append(
            Assumption(
                id="supplier_invoice_date_fixed",
                text=(
                    "The supplier invoice date does not move when delivery is late, so the "
                    f"{business.supplier_name(r.supplier) or r.supplier} invoice stays due on day {r.due_day}."
                ),
                value=float(r.due_day),
                unit="day",
                editable=False,
                source="demo_data",
            )
        )

    assumptions.append(
        Assumption(
            id="demand_flat",
            text="Walk-in demand stays at the recent daily average for the whole horizon.",
            value=plan.demand_multiplier,
            unit="multiplier",
            editable=True,
            source="demo_data",
        )
    )

    for o in business.orders:
        assumptions.append(
            Assumption(
                id="customer_payment_terms",
                text=(
                    f"{business.customer_name(o.customer) or o.customer} pays "
                    f"{o.payment_terms_days} days after delivery."
                ),
                value=float(o.payment_terms_days),
                unit="day",
                editable=True,
                source="demo_data",
            )
        )
        assumptions.append(
            Assumption(
                id="order_delivery_rule",
                text=(
                    f"{business.customer_name(o.customer) or o.customer}'s order is delivered on the first "
                    f"day stock allows on or after day {o.target_delivery_day}."
                ),
                value=float(o.target_delivery_day),
                unit="day",
                editable=False,
                source="assumed",
            )
        )

    assumptions.append(
        Assumption(
            id="lost_sales_scope",
            text=(
                "Lost walk-in sales are reported for the disrupted supplier's products; the other products "
                "are shown separately in the timeline."
            ),
            source="assumed",
            editable=False,
        )
    )

    assumptions.append(
        Assumption(
            id="horizon",
            text=f"The simulation covers {business.horizon_days} days.",
            value=float(business.horizon_days),
            unit="day",
            editable=True,
            source="user",
        )
    )

    if plan.invoice_extension_days or plan.payable_extension_days:
        assumptions.append(
            Assumption(
                id="extension_requires_supplier",
                text="A payment extension needs the supplier to agree to the new date.",
                source="assumed",
                editable=False,
            )
        )
    if plan.early_discount_pct:
        assumptions.append(
            Assumption(
                id="discount_requires_customer",
                text="An early-payment discount needs the customer to accept it and pay on delivery.",
                value=plan.early_discount_pct,
                unit="percent",
                editable=True,
                source="assumed",
            )
        )
    if plan.switch_vendor:
        assumptions.append(
            Assumption(
                id="switch_vendor_requires_supplier",
                text="Switching to the new distributor assumes the quoted price, advance and delivery day hold.",
                editable=False,
                source="assumed",
            )
        )

    if not assumptions:  # defensive: the API promises assumptions are never empty
        assumptions.append(
            Assumption(
                id="deterministic",
                text="Same inputs always produce the same result.",
                source="assumed",
            )
        )
    return assumptions
