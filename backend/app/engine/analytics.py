"""Light analytics over a :class:`Business`.

These functions answer three planning questions without running a full
simulation:

* *Who do we depend on?* — :func:`dependency_shares`
* *How long does stock last?* — :func:`stock_cover`
* *What deserves attention today?* — :func:`attention_inputs`

Everything is pure and deterministic.
"""

from __future__ import annotations

from typing import Optional

from .models import Business

SAFE_BUFFER_DAYS = 3


def dependency_shares(business: Business) -> dict:
    """Return supply concentration per product and per supplier.

    ``stock_value_share_pct`` uses opening stock valued at cost;
    ``purchase_value_share_pct`` uses inbound invoice value plus standalone
    payables within the horizon.
    """
    products_out: list[dict] = []
    for p in business.products:
        supplier = business.supplier_name(p.supplier) or "Unassigned"
        products_out.append(
            {
                "product": p.name,
                "product_id": p.id,
                "suppliers": [{"name": supplier, "share_pct": 100.0}],
            }
        )

    # Stock value by supplier.
    stock_value: dict[str, float] = {}
    for p in business.products:
        key = p.supplier or "unassigned"
        stock_value[key] = stock_value.get(key, 0.0) + p.opening_stock * p.cost_inr

    # Purchase value by supplier within the horizon.
    purchase_value: dict[str, float] = {}
    for r in business.restocks:
        if r.day <= business.horizon_days:
            purchase_value[r.supplier] = purchase_value.get(r.supplier, 0.0) + r.invoice_inr
    for pay in business.payables:
        if pay.supplier is not None and pay.due_day <= business.horizon_days:
            purchase_value[pay.supplier] = purchase_value.get(pay.supplier, 0.0) + pay.amount_inr

    total_stock = sum(stock_value.values()) or 1.0
    total_purchase = sum(purchase_value.values()) or 1.0

    suppliers: list[dict] = []
    for s in business.suppliers:
        stock_pct = round(100.0 * stock_value.get(s.id, 0.0) / total_stock, 1)
        purchase_pct = round(100.0 * purchase_value.get(s.id, 0.0) / total_purchase, 1)
        suppliers.append(
            {
                "supplier": s.name,
                "supplier_id": s.id,
                "stock_value_share_pct": stock_pct,
                "purchase_value_share_pct": purchase_pct,
                "concentration": _concentration(purchase_pct),
            }
        )

    return {"products": products_out, "supplier_dependency": suppliers}


def _concentration(pct: float) -> str:
    if pct >= 50.0:
        return "high"
    if pct >= 30.0:
        return "medium"
    return "low"


def stock_cover(business: Business, demand_multiplier: float = 1.0) -> list[dict]:
    """Return stock cover per product in days.

    ``status`` is:

    * ``safe`` — cover is longer than the wait to the next restock plus a
      3-day buffer, or the product covers the whole horizon with no restock;
    * ``critical`` — there is no restock inside the horizon and cover is short;
    * ``watch`` — everything else.
    """
    # Earliest inbound delivery per product.
    next_restock: dict[str, int] = {}
    for r in business.restocks:
        for pid in r.items:
            day = r.day
            if pid not in next_restock or day < next_restock[pid]:
                next_restock[pid] = day

    out: list[dict] = []
    for p in business.products:
        daily = p.demand_per_day * demand_multiplier
        cover = (p.opening_stock / daily) if daily > 0 else float(business.horizon_days)
        restock_day = next_restock.get(p.id)
        if restock_day is not None:
            status = "safe" if cover > restock_day + SAFE_BUFFER_DAYS else ("watch" if cover >= restock_day else "critical")
        else:
            status = "safe" if cover >= business.horizon_days else "critical"
        out.append(
            {
                "product": p.name,
                "product_id": p.id,
                "stock_units": p.opening_stock,
                "daily_demand": round(daily, 2),
                "cover_days": round(cover, 1),
                "next_restock_day": restock_day,
                "days_to_stockout": round(cover, 1),
                "status": status,
            }
        )
    return out


def attention_inputs(business: Business, demand_multiplier: float = 1.0) -> list[dict]:
    """Return the engine's part of ``/api/attention`` as plain objects.

    Person 2 merges these with anomaly flags. Each item is
    ``{kind, entity, severity, day, evidence}``.
    """
    items: list[dict] = []

    for row in stock_cover(business, demand_multiplier):
        if row["status"] == "critical":
            items.append(
                {
                    "kind": "low_cover",
                    "entity": row["product"],
                    "severity": "critical",
                    "day": row["next_restock_day"],
                    "evidence": (
                        f"{row['product']} cover is {row['cover_days']} days against a "
                        f"{row['daily_demand']}/day run-rate."
                    ),
                }
            )
        elif row["status"] == "watch":
            items.append(
                {
                    "kind": "low_cover",
                    "entity": row["product"],
                    "severity": "warning",
                    "day": row["next_restock_day"],
                    "evidence": (
                        f"{row['product']} cover is only {row['cover_days']} days; the next restock is "
                        f"day {row['next_restock_day']}."
                    ),
                }
            )

    for row in dependency_shares(business)["supplier_dependency"]:
        if row["concentration"] == "high":
            items.append(
                {
                    "kind": "supplier_concentration",
                    "entity": row["supplier"],
                    "severity": "warning",
                    "day": None,
                    "evidence": (
                        f"{row['supplier']} carries {row['purchase_value_share_pct']} percent of "
                        f"purchase value."
                    ),
                }
            )

    # Payables due against thin cash.
    free_cash = business.cash_inr
    payables = sorted(business.payables, key=lambda p: p.due_day)
    for pay in payables:
        if pay.due_day <= business.horizon_days and pay.amount_inr > free_cash * 0.5:
            items.append(
                {
                    "kind": "payable_thin_cash",
                    "entity": pay.name,
                    "severity": "warning" if pay.amount_inr <= free_cash else "critical",
                    "day": pay.due_day,
                    "evidence": (
                        f"The {_inr(pay.amount_inr)} {pay.name} is due on day {pay.due_day} while "
                        f"opening cash is {_inr(business.cash_inr)}."
                    ),
                }
            )

    return items


def _inr(value: float) -> str:
    from ..explain.reasons import format_inr

    return format_inr(value)
