"""Price what-if analysis.

Answers "what happens to profit if I change this product's price, given that
demand reacts to price?". Elasticity is an **assumption**, not a measurement —
small-business data rarely contains enough price variation to estimate it — so
results are returned as a low/base/high band.

The demand response is ``multiplier = 1 + elasticity * (price_change_pct / 100)``
(floored at zero). Sales stay supply-constrained: a stock-out still caps units.
"""

from __future__ import annotations

from .errors import ELASTICITY_OUT_OF_RANGE, UNKNOWN_PRODUCT, EngineError
from .models import Assumption, Business, Plan
from .sim import simulate_plan

ELASTICITY_MIN = -3.0
ELASTICITY_MAX = 0.0
LOW_ELASTICITY = -0.4
HIGH_ELASTICITY = -1.2


def price_whatif(
    business: Business,
    product_id: str,
    price_change_pct: float,
    elasticity: float = -0.7,
    horizon_days: int = 30,
) -> dict:
    """Return the profit impact of a price change for one product."""
    product = next((p for p in business.products if p.id == product_id), None)
    if product is None:
        raise EngineError(UNKNOWN_PRODUCT, f"No product '{product_id}' in this business.", 404)

    bands = {"low": LOW_ELASTICITY, "base": _validate_elasticity(elasticity), "high": HIGH_ELASTICITY}

    current_price = product.price_inr
    new_price = current_price * (1.0 + price_change_pct / 100.0)
    if new_price < 0:
        raise EngineError(ELASTICITY_OUT_OF_RANGE, "A price change cannot make the price negative.")

    work = business.model_copy(update={"horizon_days": int(horizon_days)})

    baseline_profit = _profit(work, product.id, current_price, 1.0)

    profit: dict[str, float] = {}
    profit_change: dict[str, float] = {}
    demand_multiplier: dict[str, float] = {}
    for name, e in bands.items():
        multiplier = max(0.0, 1.0 + e * price_change_pct / 100.0)
        demand_multiplier[name] = round(multiplier, 4)
        value = _profit(work, product.id, new_price, multiplier)
        profit[name] = round(value, 2)
        profit_change[name] = round(value - baseline_profit, 2)

    margin = current_price - product.cost_inr
    margin_after = new_price - product.cost_inr
    breakeven = _breakeven_demand_drop_pct(margin, margin_after)

    curve = []
    for change in range(-20, 21, 2):
        price_at = current_price * (1.0 + change / 100.0)
        point = {"price_change_pct": change, "profit_inr": {}, "demand_multiplier": {}}
        for name, e in bands.items():
            multiplier = max(0.0, 1.0 + e * change / 100.0)
            point["demand_multiplier"][name] = round(multiplier, 4)
            point["profit_inr"][name] = round(_profit(work, product.id, price_at, multiplier), 2)
        curve.append(point)

    sentence = _sentence(product.name, price_change_pct, breakeven, bands["base"], margin, margin_after)

    return {
        "product": product.name,
        "product_id": product.id,
        "current_price_inr": current_price,
        "new_price_inr": round(new_price, 2),
        "price_change_pct": price_change_pct,
        "elasticity": bands,
        "demand_multiplier": demand_multiplier,
        "unit_margin_inr": margin,
        "new_unit_margin_inr": round(margin_after, 2),
        "profit_inr": profit,
        "profit_change_inr": profit_change,
        "breakeven_demand_drop_pct": breakeven,
        "horizon_days": int(horizon_days),
        "curve": curve,
        "sentence": sentence,
        "assumptions": [
            Assumption(
                id="price_elasticity",
                text=(
                    "Price elasticity of demand is assumed, not measured from the business's own data: "
                    f"low {LOW_ELASTICITY}, base {bands['base']}, high {HIGH_ELASTICITY}."
                ),
                value=bands["base"],
                unit="elasticity",
                editable=True,
                source="assumed",
            ),
            Assumption(
                id="supply_constrained_sales",
                text="Sales stay limited by available stock; a stock-out still caps units sold.",
                source="assumed",
            ),
        ],
    }


def _validate_elasticity(elasticity: float) -> float:
    if elasticity < ELASTICITY_MIN or elasticity > ELASTICITY_MAX:
        raise EngineError(
            ELASTICITY_OUT_OF_RANGE,
            f"Elasticity must be between {ELASTICITY_MIN} and {ELASTICITY_MAX}.",
        )
    return elasticity


def _profit(business: Business, product_id: str, price: float, demand_multiplier: float) -> float:
    """Profit for one product over the horizon under a price and demand shift."""
    product = next(p for p in business.products if p.id == product_id)
    modified = [
        p.model_copy(update={"price_inr": price}) if p.id == product_id else p for p in business.products
    ]
    work = business.model_copy(update={"products": modified})
    result = simulate_plan(work, Plan(demand_multiplier=demand_multiplier), light=True)
    units = result.details.get("units_sold", {}).get(product_id, 0.0)
    return units * (price - product.cost_inr)


def _breakeven_demand_drop_pct(margin: float, margin_after: float) -> float | None:
    """The demand fall at which profit is unchanged: ``1 - m/(m + dp)``."""
    if margin_after <= 0:
        return None
    if margin + (margin_after - margin) == 0:
        return None
    return round(100.0 * (1.0 - margin / margin_after), 2)


def _sentence(name, change, breakeven, base_elasticity, margin, margin_after) -> str:
    direction = "rise" if change >= 0 else "cut"
    if breakeven is None:
        return (
            f"A {abs(change):g}% price {direction} for {name} does not pay off at any demand level: "
            f"the unit margin would fall from {margin:g} to {margin_after:g} rupees."
        )
    return (
        f"A {abs(change):g}% price {direction} for {name} keeps profit level if demand falls by no more "
        f"than {breakeven:g}% (unit margin {margin:g} to {margin_after:g} rupees), "
        f"assuming an elasticity of {base_elasticity:g}."
    )
