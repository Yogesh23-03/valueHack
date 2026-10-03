"""Explanation coverage and rupee formatting tests."""

from __future__ import annotations

import pytest

from app.engine.models import Plan, Shock
from app.explain.reasons import (
    COUNT,
    DAY,
    INR,
    display_value,
    format_inr,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, "₹0"),
        (999, "₹999"),
        (1000, "₹1,000"),
        (100000, "₹1,00,000"),
        (177600, "₹1,77,600"),
        (275000, "₹2,75,000"),
        (-171600, "₹-1,71,600"),
        (-29225, "₹-29,225"),
    ],
)
def test_format_inr(value, expected):
    assert format_inr(value) == expected


def test_every_summary_metric_has_an_explanation(business):
    from app.engine.sim import simulate_plan

    result = simulate_plan(business, Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=14)))
    explained = {e.metric_id for e in result.explanations}
    assert set(result.summary.keys()) <= explained, set(result.summary) - explained


def test_each_sentence_contains_its_value(business):
    from app.engine.sim import simulate_plan

    for plan in [
        Plan(),
        Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=14)),
        Plan(shock=Shock(type="cost_spike", target="sup_a", magnitude=30)),
    ]:
        result = simulate_plan(business, plan)
        for exp in result.explanations:
            shown = display_value(exp.unit, exp.value)
            if shown is not None:
                assert shown in exp.sentence, (exp.metric_id, shown, exp.sentence)


def test_assumptions_are_never_empty(business):
    from app.engine.sim import simulate_plan

    for plan in [Plan(), Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=14))]:
        result = simulate_plan(business, plan)
        assert result.assumptions


def test_key_sentences_are_plain_language(business):
    from app.engine.sim import simulate_plan

    result = simulate_plan(business, Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=14)))
    by_metric = {e.metric_id: e.sentence for e in result.explanations}

    assert "day 10" in by_metric["stockout_day"]
    assert "day 8" in by_metric["stockout_day"] and "day 22" in by_metric["stockout_day"]
    assert "₹1,77,600" in by_metric["lost_sales_inr"]
    assert "day 22" in by_metric["order_delay_days"] and "day 12" in by_metric["order_delay_days"]
    assert "₹2,75,000" in by_metric["first_negative_day"]
    assert "Supplier C" in by_metric["failed_payments_count"]


def test_units_are_constant():
    assert (INR, DAY, COUNT) == ("inr", "day", "count")
