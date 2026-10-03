"""The three README headline numbers, plus the cascade chain order.

README: for a 14-day Supplier A delay the demo gives a stock-out on day 10,
cash below zero on day 23 and a failed Supplier C payment on day 25.
"""

from __future__ import annotations

from app.engine.models import Plan, Shock


def test_headline_numbers(business):
    from app.engine.sim import simulate_plan

    result = simulate_plan(business, Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=14)))
    s = result.summary

    assert s["stockout_day"] == 10
    assert s["first_negative_day"] == 23
    failed = {(f["name"], f["day"]) for f in result.details["failed_payments"]}
    assert ("Supplier C invoice", 25) in failed


def test_cascade_chain_order_and_days(business):
    from app.engine.sim import simulate_plan

    result = simulate_plan(business, Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=14)))
    chain = result.cascade_chain

    assert [step.step for step in chain] == [
        "supplier_delay",
        "inventory_shortage",
        "delayed_orders",
        "customer_payment_delay",
        "cash_gap",
        "failed_supplier_payment",
    ]
    by_step = {step.step: step for step in chain}
    assert by_step["supplier_delay"].status == "triggered"
    assert by_step["supplier_delay"].day == 8
    assert by_step["inventory_shortage"].day == 10
    assert by_step["delayed_orders"].day == 22
    assert by_step["customer_payment_delay"].day == 29
    assert by_step["cash_gap"].day == 23
    assert by_step["failed_supplier_payment"].day == 25


def test_headline_over_http(client):
    r = client.post("/api/simulate/cascade", json={"delay": 14})
    assert r.status_code == 200
    body = r.json()
    assert body["stockout"] == 10
    assert body["first_negative_day"] == 23
    assert any(f["name"] == "Supplier C invoice" and f["day"] == 25 for f in body["failed"])
