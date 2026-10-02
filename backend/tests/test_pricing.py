"""Price what-if tests, including one hand calculation.

Fans: price 1,900 and cost 1,400, so the unit margin is 500.
A +10 percent price change makes the price 2,090 and the margin 690.
At elasticity -0.7 the demand multiplier is 1 + (-0.7 * 0.10) = 0.93.
"""

from __future__ import annotations

import pytest

from app.engine.errors import EngineError


def test_fans_plus_ten_percent(business):
    from app.engine.pricing import price_whatif

    out = price_whatif(business, "fans", 10.0, elasticity=-0.7)
    assert out["demand_multiplier"]["base"] == pytest.approx(0.93)
    assert out["unit_margin_inr"] == 500
    assert out["new_unit_margin_inr"] == 690
    assert out["new_price_inr"] == 2090
    assert out["breakeven_demand_drop_pct"] == pytest.approx(27.54, abs=0.01)
    # Break-even: 1 - m/(m+dp) = 1 - 500/690 = 0.2754 -> 27.54 percent.
    assert out["elasticity"] == {"low": -0.4, "base": -0.7, "high": -1.2}


def test_curve_has_21_points(business):
    from app.engine.pricing import price_whatif

    out = price_whatif(business, "fans", 10.0)
    assert len(out["curve"]) == 21
    assert out["curve"][0]["price_change_pct"] == -20
    assert out["curve"][-1]["price_change_pct"] == 20
    for point in out["curve"]:
        assert set(point["profit_inr"].keys()) == {"low", "base", "high"}


def test_pricing_assumption_is_labelled(business):
    from app.engine.pricing import price_whatif

    out = price_whatif(business, "fans", 10.0)
    sources = {a.id: a.source for a in out["assumptions"]}
    assert sources["price_elasticity"] == "assumed"


def test_unknown_product(business):
    from app.engine.pricing import price_whatif

    with pytest.raises(EngineError):
        price_whatif(business, "rockets", 10.0)
