"""The day-by-day BizSim simulator.

One disruption spreads through a business like this::

    supplier delay -> inventory shortage -> delayed orders
    -> customer payment delay -> cash-flow gap -> failed supplier payment

Everything the engine reports is computed here from a
:class:`~app.engine.models.Business` and a :class:`~app.engine.models.Plan`.
The engine is deterministic and pure: no randomness, no clock, no network.

Daily order of events (as agreed with the product spec):

1. receive stock (restock arrives)
2. deliver customer orders on the first day stock allows
3. sell to walk-ins (unmet demand is lost)
4. add cash from sales and receivables due
5. subtract daily running costs
6. pay payables due (a shortfall records a failed payment *and* still deducts
   the amount, so the size of the gap stays visible)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from .errors import (
    INVALID_SHOCK,
    MAGNITUDE_OUT_OF_RANGE,
    UNKNOWN_CUSTOMER,
    UNKNOWN_PRODUCT,
    UNKNOWN_SUPPLIER,
    EngineError,
)
from .models import (
    Assumption,
    Business,
    CascadeStep,
    Event,
    Plan,
    Shock,
    SimResult,
)

META_ENGINE_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Internal simulation helpers
# ---------------------------------------------------------------------------


@dataclass
class _Payable:
    """A payment the business must make on a day."""

    id: str
    name: str
    amount_inr: float
    due_day: int
    supplier: Optional[str] = None
    kind: str = "standalone"  # restock | standalone | advance | balance


@dataclass
class _Receivable:
    """A customer payment tied to a delivered order."""

    order_id: str
    customer: str
    name: str
    amount_inr: float
    normal_pay_day: int
    pay_day: Optional[int] = None
    delivered_day: Optional[int] = None
    delivered: bool = False
    received: bool = False


@dataclass
class _StockoutRun:
    """Accumulates one continuous run of lost walk-in sales for a product."""

    product: str
    start_day: int
    end_day: int
    units: float = 0.0
    value_inr: float = 0.0
    event_id: Optional[str] = None


class _EventLog:
    """Small helper that assigns stable ids and keeps insertion order."""

    def __init__(self) -> None:
        self.events: list[Event] = []
        self._n = 0

    def add(
        self,
        day: int,
        type_: str,
        entity: str,
        values: Optional[dict] = None,
        cause_ids: Optional[list[str]] = None,
        severity: str = "info",
    ) -> str:
        self._n += 1
        eid = f"ev{self._n:03d}"
        self.events.append(
            Event(
                id=eid,
                day=day,
                type=type_,
                entity=entity,
                values=values or {},
                cause_ids=cause_ids or [],
                severity=severity,  # type: ignore[arg-type]
            )
        )
        return eid

    def first(self, type_: str, entity: Optional[str] = None) -> Optional[Event]:
        for e in self.events:
            if e.type == type_ and (entity is None or e.entity == entity):
                return e
        return None

    def by_type(self, type_: str, entity: Optional[str] = None) -> list[Event]:
        return [e for e in self.events if e.type == type_ and (entity is None or e.entity == entity)]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate_plan(business: Business, plan: Plan) -> None:
    """Raise :class:`EngineError` for anything the simulator cannot run."""
    supplier_ids = {s.id for s in business.suppliers}
    customer_ids = {c.id for c in business.customers}
    product_ids = {p.id for p in business.products}

    shock = plan.shock
    if shock is not None:
        if shock.type not in ("supplier_delay", "customer_delay", "cost_spike", "demand_shock"):
            raise EngineError(INVALID_SHOCK, f"Unknown scenario type '{shock.type}'.")
        if shock.type in ("supplier_delay", "cost_spike"):
            if shock.target and shock.target not in supplier_ids:
                raise EngineError(
                    UNKNOWN_SUPPLIER,
                    f"No supplier '{shock.target}' in this business.",
                    404,
                )
            if shock.magnitude < 0:
                raise EngineError(INVALID_SHOCK, "Delay and price change cannot be negative.")
            if shock.type == "supplier_delay" and shock.magnitude > 180:
                raise EngineError(
                    MAGNITUDE_OUT_OF_RANGE,
                    "A supplier delay above 180 days is outside the supported range.",
                )
            if shock.type == "cost_spike" and shock.magnitude > 500:
                raise EngineError(
                    MAGNITUDE_OUT_OF_RANGE,
                    "A cost spike above 500 percent is outside the supported range.",
                )
        elif shock.type == "customer_delay":
            if shock.target and shock.target not in customer_ids:
                raise EngineError(
                    UNKNOWN_CUSTOMER,
                    f"No customer '{shock.target}' in this business.",
                    404,
                )
            if shock.magnitude < 0:
                raise EngineError(INVALID_SHOCK, "A customer delay cannot be negative.")
            if shock.magnitude > 180:
                raise EngineError(
                    MAGNITUDE_OUT_OF_RANGE,
                    "A customer delay above 180 days is outside the supported range.",
                )
        elif shock.type == "demand_shock":
            if shock.magnitude < -100 or shock.magnitude > 500:
                raise EngineError(
                    MAGNITUDE_OUT_OF_RANGE,
                    "A demand change must be between -100 and 500 percent.",
                )

    if plan.demand_multiplier < 0:
        raise EngineError(INVALID_SHOCK, "Demand multiplier cannot be negative.")
    if plan.early_discount_pct < 0 or plan.early_discount_pct > 100:
        raise EngineError(MAGNITUDE_OUT_OF_RANGE, "A discount must be between 0 and 100 percent.")
    if plan.invoice_extension_days < 0 or plan.payable_extension_days < 0:
        raise EngineError(INVALID_SHOCK, "An extension cannot be negative.")

    if plan.discount_customer and plan.discount_customer not in customer_ids:
        raise EngineError(UNKNOWN_CUSTOMER, f"No customer '{plan.discount_customer}'.", 404)
    if plan.invoice_extension_supplier and plan.invoice_extension_supplier not in supplier_ids:
        raise EngineError(UNKNOWN_SUPPLIER, f"No supplier '{plan.invoice_extension_supplier}'.", 404)
    if plan.payable_extension_target and plan.payable_extension_target not in supplier_ids:
        raise EngineError(UNKNOWN_SUPPLIER, f"No supplier '{plan.payable_extension_target}'.", 404)

    for pid in list(plan_walk_in_products(business)):
        if pid not in product_ids:
            raise EngineError(UNKNOWN_PRODUCT, f"No product '{pid}'.", 404)


def plan_walk_in_products(business: Business) -> Iterable[str]:
    return (p.id for p in business.products)


# ---------------------------------------------------------------------------
# Schedule construction
# ---------------------------------------------------------------------------


def _switched_restock(business: Business, switched_supplier: Optional[str]):
    for r in business.restocks:
        if switched_supplier is None or r.supplier == switched_supplier:
            return r
    return business.restocks[0] if business.restocks else None


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------


def simulate_plan(
    business: Business,
    plan: Plan,
    *,
    with_ranges: bool = False,
    light: bool = False,
) -> SimResult:
    """Run one simulation of ``plan`` against ``business``.

    Returns a fully populated :class:`SimResult`. When ``with_ranges`` is true
    the result also carries the low/base/high demand bands. ``light`` skips the
    explanation/cascade/assumption composition for internal rate runs.
    """
    _validate_plan(business, plan)

    shock = plan.shock
    horizon = business.horizon_days
    daily_costs = business.daily_costs_inr

    # --- resolve scenario effects -----------------------------------------
    if shock and shock.type in ("supplier_delay", "cost_spike") and shock.target:
        target_supplier = shock.target
    else:
        target_supplier = business.primary_supplier
    delay_days = (
        int(shock.magnitude)
        if shock and shock.type == "supplier_delay" and (not shock.target or shock.target == target_supplier)
        else 0
    )
    cost_spike_pct = (
        shock.magnitude
        if shock and shock.type == "cost_spike" and (not shock.target or shock.target == target_supplier)
        else 0.0
    )
    customer_late = (
        int(shock.magnitude)
        if shock and shock.type == "customer_delay"
        else 0
    )
    demand_shock_pct = (
        shock.magnitude if shock and shock.type == "demand_shock" else 0.0
    )

    log = _EventLog()

    # --- restock schedule --------------------------------------------------
    arrivals: list[tuple[int, str, dict[str, float]]] = []  # (day, supplier, items)
    payables: list[_Payable] = []
    slipped_restock = False

    switched_supplier = target_supplier if plan.switch_vendor else None
    restock_to_switch = _switched_restock(business, target_supplier) if plan.switch_vendor else None

    for r in business.restocks:
        if plan.switch_vendor and (switched_supplier is None or r.supplier == switched_supplier):
            continue
        arrival_day = r.day + (delay_days if r.supplier == target_supplier else 0)
        invoice = r.invoice_inr
        if cost_spike_pct and r.supplier == target_supplier:
            invoice = invoice * (1.0 + cost_spike_pct / 100.0)
        due_day = r.due_day
        if (
            plan.invoice_extension_days
            and r.supplier == target_supplier
            and (plan.invoice_extension_supplier is None or plan.invoice_extension_supplier == r.supplier)
        ):
            due_day += plan.invoice_extension_days
        supplier_name = business.supplier_name(r.supplier) or r.supplier
        if arrival_day != r.day:
            slipped_restock = True
            log.add(
                r.day,
                "restock_slipped",
                supplier_name,
                {"scheduled_day": r.day, "actual_day": arrival_day, "days_late": arrival_day - r.day},
                severity="warning",
            )
        arrivals.append((arrival_day, r.supplier, dict(r.items)))
        payables.append(
            _Payable(
                id=f"pay-{r.supplier}",
                name=f"{supplier_name} invoice",
                amount_inr=invoice,
                due_day=due_day,
                supplier=r.supplier,
                kind="restock",
            )
        )

    # Standalone payables (for example the Supplier C invoice).
    for p in business.payables:
        due = p.due_day
        if plan.payable_extension_days and (
            plan.payable_extension_target is None or p.supplier == plan.payable_extension_target
        ):
            due += plan.payable_extension_days
        payables.append(
            _Payable(
                id=f"pay-standalone-{p.supplier or p.name}",
                name=p.name,
                amount_inr=p.amount_inr,
                due_day=due,
                supplier=p.supplier,
                kind="standalone",
            )
        )

    # Alternative vendor replaces the switched restock.
    if plan.switch_vendor and business.alternative_vendor is not None:
        alt = business.alternative_vendor
        restock = restock_to_switch
        base_cost = restock.invoice_inr if restock else 0.0
        cost = base_cost * (1.0 - alt.price_discount_pct / 100.0)
        advance = cost * alt.advance_pct / 100.0
        balance = cost - advance
        payables.append(
            _Payable("pay-alt-advance", f"{alt.name} advance", advance, alt.advance_day, alt.id, "advance")
        )
        payables.append(
            _Payable(
                "pay-alt-balance",
                f"{alt.name} balance",
                balance,
                alt.delivery_day + alt.balance_due_days,
                alt.id,
                "balance",
            )
        )
        if not plan.vendor_fails and restock is not None:
            arrivals.append((alt.delivery_day, alt.id, dict(restock.items)))

    # --- orders / receivables ---------------------------------------------
    receivables: list[_Receivable] = []
    for o in business.orders:
        customer_name = business.customer_name(o.customer) or o.customer
        discount = (
            plan.early_discount_pct
            if plan.discount_customer in (None, o.customer) and plan.early_discount_pct
            else 0.0
        )
        amount = o.amount_inr * (1.0 - discount / 100.0)
        normal_day = o.target_delivery_day + o.payment_terms_days
        shock_target = shock.target if shock else None
        late = customer_late if (not shock_target or shock_target == o.customer) else 0
        if discount:
            pay_day_normal = o.target_delivery_day  # paid on delivery
        else:
            pay_day_normal = normal_day + late
        receivables.append(
            _Receivable(
                order_id=o.id,
                customer=o.customer,
                name=customer_name,
                amount_inr=amount,
                normal_pay_day=pay_day_normal,
            )
        )
        if discount:
            log.add(
                0,
                "discount_agreed",
                customer_name,
                {"discount_pct": discount, "amount_inr": amount},
                severity="info",
            )

    # --- lost-sales scope --------------------------------------------------
    scope_supplier = target_supplier
    if scope_supplier is None:
        scope_ids = None
    else:
        scope_ids = {p.id for p in business.products if p.supplier == scope_supplier}

    # --- state -------------------------------------------------------------
    stock = {p.id: float(p.opening_stock) for p in business.products}
    demand = {
        p.id: max(0.0, p.demand_per_day * plan.demand_multiplier * (1.0 + demand_shock_pct / 100.0))
        for p in business.products
    }
    products = {p.id: p for p in business.products}

    cash = business.cash_inr
    cash_timeline: list[float] = []
    stock_timeline: list[dict[str, float]] = []

    first_negative_day: Optional[int] = None
    lowest_cash = float("inf")
    lowest_cash_day = 0

    lost_sales_total = 0.0
    lost_sales_scoped = 0.0
    units_sold: dict[str, float] = {p.id: 0.0 for p in business.products}
    stockout_day: Optional[int] = None  # scoped to the disrupted supply chain
    stockout_runs: dict[str, _StockoutRun] = {}
    active_runs: dict[str, _StockoutRun] = {}
    arrivals_by_day: dict[int, list[tuple[int, str, dict[str, float]]]] = {}
    for a in arrivals:
        arrivals_by_day.setdefault(a[0], []).append(a)

    failed_payments: list[dict] = []
    stockout_event_id: dict[str, str] = {}

    # First event: the invoice-date assumption, recorded for transparency.
    _ = log

    for day in range(1, horizon + 1):
        # 1. receive stock
        for _day, supplier_id, items in sorted(arrivals_by_day.get(day, []), key=lambda t: t[1]):
            for pid, qty in items.items():
                if pid in stock:
                    stock[pid] += qty
            supplier_name = business.supplier_name(supplier_id) or supplier_id
            log.add(day, "restock_arrived", supplier_name, {"units": sum(items.values())}, severity="info")

        # 2. deliver orders on the first day stock allows
        for rec in receivables:
            if rec.delivered:
                continue
            o = next(x for x in business.orders if x.id == rec.order_id)
            if day < o.target_delivery_day:
                continue
            if all(stock.get(pid, 0.0) >= qty for pid, qty in o.items.items()):
                for pid, qty in o.items.items():
                    stock[pid] = stock.get(pid, 0.0) - qty
                rec.delivered = True
                rec.delivered_day = day
                rec.pay_day = rec.normal_pay_day + max(0, day - o.target_delivery_day)
                log.add(
                    day,
                    "order_delivered",
                    rec.name,
                    {"order_id": rec.order_id, "target_day": o.target_delivery_day},
                    severity="info",
                )
                if day > o.target_delivery_day:
                    log.add(
                        day,
                        "order_delayed",
                        rec.name,
                        {
                            "order_id": rec.order_id,
                            "target_day": o.target_delivery_day,
                            "delivered_day": day,
                            "days_late": day - o.target_delivery_day,
                        },
                        severity="warning",
                    )

        # 3. walk-in sales
        day_lost = 0.0
        for pid, product in products.items():
            want = demand[pid]
            available = stock.get(pid, 0.0)
            if available >= want:
                stock[pid] = available - want
                cash += want * product.price_inr
                units_sold[pid] += want
            else:
                sold = available
                lost_units = want - sold
                stock[pid] = 0.0
                cash += sold * product.price_inr
                units_sold[pid] += sold
                lost_value = lost_units * product.price_inr
                lost_sales_total += lost_value
                if scope_ids is None or pid in scope_ids:
                    lost_sales_scoped += lost_value
                day_lost += lost_value
                if scope_ids is None or pid in scope_ids:
                    if stockout_day is None:
                        stockout_day = day
                if pid not in stockout_event_id:
                    log.add(
                        day,
                        "stockout_started",
                        product.name,
                        {"product_id": pid, "demand": round(want, 2), "available": round(available, 2)},
                        cause_ids=[e.id for e in log.by_type("restock_slipped")],
                        severity="critical",
                    )
                    stockout_event_id[pid] = log.events[-1].id
                run = active_runs.get(pid)
                if run is None:
                    run = _StockoutRun(product=pid, start_day=day, end_day=day)
                    active_runs[pid] = run
                    stockout_runs.setdefault(pid, run)
                run.end_day = day
                run.units += lost_units
                run.value_inr += lost_value

        # 4. receivables due
        for rec in receivables:
            if not rec.delivered or rec.received:
                continue
            if rec.pay_day is not None and day == rec.pay_day:
                cash += rec.amount_inr
                rec.received = True
                log.add(day, "receivable_received", rec.name, {"amount_inr": rec.amount_inr}, severity="info")
                o = next(x for x in business.orders if x.id == rec.order_id)
                if rec.pay_day is not None and rec.pay_day > o.target_delivery_day + o.payment_terms_days:
                    delivered_ev = log.first("order_delivered", rec.name)
                    log.add(
                        day,
                        "receivable_pushed",
                        rec.name,
                        {
                            "normal_day": o.target_delivery_day + o.payment_terms_days,
                            "actual_day": day,
                        },
                        cause_ids=[delivered_ev.id] if delivered_ev else [],
                        severity="warning",
                    )

        # 5. daily running costs
        cash -= daily_costs

        # 6. payables due
        for pay in sorted(payables, key=lambda p: (p.due_day, p.id)):
            if day != pay.due_day:
                continue
            if cash >= pay.amount_inr:
                cash -= pay.amount_inr
                log.add(day, "payable_paid", pay.name, {"amount_inr": pay.amount_inr}, severity="info")
            else:
                available = cash
                cash -= pay.amount_inr  # still deduct so the gap stays visible
                failed_payments.append({"name": pay.name, "day": day})
                pushed = log.first("receivable_pushed")
                log.add(
                    day,
                    "payable_failed",
                    pay.name,
                    {
                        "amount_inr": pay.amount_inr,
                        "available_inr": round(available, 2),
                        "shortfall_inr": round(pay.amount_inr - available, 2),
                        "kind": pay.kind,
                    },
                    cause_ids=[pushed.id] if pushed else [],
                    severity="critical",
                )

        if cash < 0 and first_negative_day is None:
            first_negative_day = day
            failed_so_far = [e.id for e in log.by_type("payable_failed")]
            log.add(
                day,
                "cash_negative",
                "cash",
                {"cash_inr": round(cash, 2)},
                cause_ids=failed_so_far,
                severity="critical",
            )

        if cash < lowest_cash:
            lowest_cash = cash
            lowest_cash_day = day

        cash_timeline.append(round(cash, 2))
        stock_timeline.append({pid: round(stock[pid], 2) for pid in stock})

    # Close any still-open lost-sales runs with a summary event.
    for run in stockout_runs.values():
        product = products[run.product]
        cause = [stockout_event_id[run.product]] if run.product in stockout_event_id else []
        log.add(
            run.end_day,
            "sales_lost",
            product.name,
            {
                "product_id": run.product,
                "days": run.end_day - run.start_day + 1,
                "units": round(run.units, 2),
                "value_inr": round(run.value_inr, 2),
            },
            cause_ids=cause,
            severity="critical",
        )

    if lowest_cash == float("inf"):
        lowest_cash = cash

    # --- summary -----------------------------------------------------------
    order_delay_days: Optional[int] = None
    customer_payment_day: Optional[int] = None
    for rec in receivables:
        o = next(x for x in business.orders if x.id == rec.order_id)
        if rec.delivered and rec.delivered_day is not None and rec.delivered_day > o.target_delivery_day:
            lateness = rec.delivered_day - o.target_delivery_day
            if order_delay_days is None or lateness > order_delay_days:
                order_delay_days = lateness
        if rec.pay_day is not None:
            if customer_payment_day is None or rec.pay_day > customer_payment_day:
                customer_payment_day = rec.pay_day

    summary = {
        "stockout_day": stockout_day,
        "lost_sales_inr": round(lost_sales_scoped, 2),
        "lost_sales_all_products_inr": round(lost_sales_total, 2),
        "first_negative_day": first_negative_day,
        "lowest_cash_inr": round(lowest_cash, 2),
        "lowest_cash_day": lowest_cash_day,
        "end_cash_inr": round(cash, 2),
        "failed_payments_count": len(failed_payments),
        "order_delay_days": order_delay_days,
        "customer_payment_day": customer_payment_day,
    }

    details = {
        "lost_sales_scoped_inr": round(lost_sales_scoped, 2),
        "lost_sales_all_inr": round(lost_sales_total, 2),
        "failed_payments": failed_payments,
        "delivered_orders": [
            {"order_id": r.order_id, "delivered_day": r.delivered_day, "pay_day": r.pay_day}
            for r in receivables
        ],
        "lost_sales_products": {
            pid: {
                "start_day": run.start_day,
                "end_day": run.end_day,
                "days": run.end_day - run.start_day + 1,
                "value_inr": round(run.value_inr, 2),
            }
            for pid, run in stockout_runs.items()
        },
        "stockout_products": [
            {
                "product_id": pid,
                "day": next((e.day for e in log.events if e.id == eid), None),
            }
            for pid, eid in stockout_event_id.items()
        ],
        "initial_cash_inr": business.cash_inr,
        "scope_supplier": scope_supplier,
        "units_sold": {pid: round(u, 2) for pid, u in units_sold.items()},
    }

    # Explanations, cascade chain and assumptions are composed by the explain
    # layer from the raw result. Light runs skip this for internal rate loops.
    if light:
        explanations = []
        cascade_chain = []
        assumptions = []
    else:
        from ..explain.reasons import build_assumptions, build_cascade_chain, build_explanations

        explanations = build_explanations(business, plan, summary, log.events, details)
        cascade_chain = build_cascade_chain(business, plan, summary, log.events, details)
        assumptions = build_assumptions(business, plan)

    result = SimResult(
        scenario=_scenario_dict(business, plan),
        summary=summary,
        cascade_chain=cascade_chain,
        events=log.events,
        timeline={"cash": cash_timeline, "stock": stock_timeline},
        explanations=explanations,
        assumptions=assumptions,
        meta={
            "engine_version": META_ENGINE_VERSION,
            "horizon_days": horizon,
            "deterministic": True,
            "shock_type": plan.shock_type(),
        },
        details=details,
    )

    if with_ranges:
        from .ranges import compute_ranges

        result.ranges = compute_ranges(business, plan)
    else:
        from .models import Ranges

        result.ranges = Ranges()

    return result


def _scenario_dict(business: Business, plan: Plan) -> dict:
    shock = plan.shock
    return {
        "type": shock.type if shock else "none",
        "target": shock.target if shock else "",
        "target_name": business.supplier_name(shock.target) if shock and shock.type != "customer_delay" else (
            business.customer_name(shock.target) if shock else None
        ),
        "magnitude": shock.magnitude if shock else 0,
        "label": plan.label,
        "switch_vendor": plan.switch_vendor,
        "vendor_fails": plan.vendor_fails,
        "early_discount_pct": plan.early_discount_pct,
        "invoice_extension_days": plan.invoice_extension_days,
        "payable_extension_days": plan.payable_extension_days,
        "demand_multiplier": plan.demand_multiplier,
    }


# ---------------------------------------------------------------------------
# Convenience entry points
# ---------------------------------------------------------------------------


def simulate_shock(
    business: Business,
    shock: Optional[Shock] = None,
    *,
    demand_multiplier: float = 1.0,
    with_ranges: bool = False,
    plan_kwargs: Optional[dict] = None,
) -> SimResult:
    """Simulate a shock with no preventive actions."""
    plan = Plan(shock=shock, demand_multiplier=demand_multiplier, **(plan_kwargs or {}))
    return simulate_plan(business, plan, with_ranges=with_ranges)
