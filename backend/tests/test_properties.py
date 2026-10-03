"""Property tests.

These check invariants that must hold for any delay, not just the oracle rows.
"""

from __future__ import annotations

import copy

from app.engine.models import Plan, Shock


def _run(business, delay):
    from app.engine.sim import simulate_plan

    return simulate_plan(business, Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=delay)))


def test_stockout_day_never_gets_later_as_delay_grows(business):
    # As Supplier A slips more, stock runs out earlier or on the same day.
    days = []
    for delay in [0, 2, 5, 10, 14, 20, 30]:
        days.append(_run(business, delay).summary["stockout_day"])
    assert days == sorted(days, reverse=True), days


def test_lost_sales_never_decrease_as_delay_grows(business):
    lost = []
    for delay in [0, 2, 5, 10, 14, 20, 30]:
        lost.append(_run(business, delay).summary["lost_sales_inr"])
    assert lost == sorted(lost), lost


def test_baseline_has_no_failed_payment(business):
    result = _run(business, 0)
    assert result.summary["failed_payments_count"] == 0
    assert result.summary["first_negative_day"] is None


def test_cash_timeline_length_equals_horizon(business):
    for horizon in [10, 30, 45]:
        plan = Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=14))
        work = business.model_copy(update={"horizon_days": horizon})
        from app.engine.sim import simulate_plan

        result = simulate_plan(work, plan)
        assert len(result.timeline["cash"]) == horizon
        assert len(result.timeline["stock"]) == horizon


def test_ranges_contain_the_base_value(business):
    from app.engine.sim import simulate_plan

    result = simulate_plan(business, Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=14)), with_ranges=True)
    base = next(r for r in result.ranges.runs if r.case == "base")
    assert base.metrics["stockout_day"] == result.summary["stockout_day"]
    assert base.metrics["lowest_cash_inr"] == result.summary["lowest_cash_inr"]
    for key, metric in result.ranges.metrics.items():
        vals = [v for v in (metric.min, metric.base, metric.max) if v is not None]
        if metric.min is not None and metric.max is not None:
            assert metric.min <= metric.max, key
        assert metric.base in vals, key


def test_simulation_is_deterministic(business):
    from app.engine.sim import simulate_plan

    plan = Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=14))
    first = simulate_plan(business, plan)
    second = simulate_plan(copy.deepcopy(business), plan)
    assert first.summary == second.summary
    assert first.timeline == second.timeline
    assert [e.model_dump() for e in first.events] == [e.model_dump() for e in second.events]
