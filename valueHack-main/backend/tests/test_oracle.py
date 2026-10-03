"""The oracle table.

Every row is the reference output for the Sharma Hardware demo. The arithmetic
is written out in comments so a reader can check each number by hand.

Reference facts
---------------
* Daily running cost = fixed 3000 + other supplies 1800 = 4,800.
* Full-day walk-in sales = fans 4*1900 + wiring 6*1200 + switches 15*170
  = 7,600 + 7,200 + 2,550 = 17,350, so a full day nets +12,550.
* When fans and wiring are out, only switches sell: 2,550 - 4,800 = -2,250/day.
* One day of lost fans+wiring walk-in sales = 4*1900 + 6*1200 = 14,800.
* Supplier A invoice = 100*1400 + 150*900 = 2,75,000, due day 23.
* Supplier C payable = 70,000, due day 25.
* Verma's order = 20*1900 + 30*1200 = 74,000, delivered on the first day stock
  allows on or after day 12, paid 7 days later.
"""

from __future__ import annotations

import pytest

from app.engine.models import Plan, Shock

A = "sup_a"
VERMA = "verma"


def _plan(**kwargs) -> Plan:
    return Plan(**kwargs)


def _delay(days: int) -> Shock:
    return Shock(type="supplier_delay", target=A, magnitude=days)


CASES = [
    # (label, plan, stockout, lost, first_negative, lowest_cash, lowest_day, failed_names)
    (
        "baseline",
        _plan(),
        30,          # fans & wiring deplete on day 30 after the Verma delivery on day 12
        14800,       # one day (day 30) of fans+wiring lost
        None,
        62550,       # day 1: 50,000 + 17,350 - 4,800
        1,
        [],
    ),
    (
        "delay14",
        _plan(shock=_delay(14)),
        10,          # stock runs out end of day 9, first lost day is 10
        177600,      # 12 lost days (10..21) * 14,800
        23,          # A invoice 2,75,000 due with only 1,53,400 available
        -171600,     # day 25 after Supplier C's 70,000 is also deducted
        25,
        ["Supplier A invoice", "Supplier C invoice"],
    ),
    (
        "delay14_extA14",
        _plan(shock=_delay(14), invoice_extension_days=14, invoice_extension_supplier=A),
        10,
        177600,
        None,        # invoice due day 37, outside the horizon
        62550,
        1,
        [],
    ),
    (
        "delay14_discount3",
        _plan(shock=_delay(14), early_discount_pct=3.0, discount_customer=VERMA),
        10,
        177600,
        23,
        -99820,      # Verma pays 71,780 on day 22, softening the day-23 gap
        25,
        ["Supplier A invoice", "Supplier C invoice"],
    ),
    (
        "delay14_ext_discount",
        _plan(
            shock=_delay(14),
            invoice_extension_days=14,
            invoice_extension_supplier=A,
            early_discount_pct=3.0,
            discount_customer=VERMA,
        ),
        10,
        177600,
        None,
        62550,
        1,
        [],
    ),
    (
        "delay14_switch",
        _plan(shock=_delay(14), switch_vendor=True),
        30,          # new distributor restocks on day 6
        14800,
        3,           # advance 1,16,875 vs 87,650 cash on day 3
        -29225,      # 87,650 - 1,16,875
        3,
        ["New Distributor advance"],
    ),
    (
        "delay14_switch_fails",
        _plan(shock=_delay(14), switch_vendor=True, vendor_fails=True),
        10,
        310800,      # 21 lost days (10..30) * 14,800
        3,
        -213550,     # day 30 after advance, balance day 21 and Supplier C day 25
        30,
        ["New Distributor advance", "New Distributor balance", "Supplier C invoice"],
    ),
    (
        "costspike15",
        _plan(shock=Shock(type="cost_spike", target=A, magnitude=15)),
        30,
        14800,
        None,
        38750,       # 2,75,000 * 1.15 = 3,16,250 due day 23, thin day-25 cash after C
        25,
        [],
    ),
    (
        "costspike30",
        _plan(shock=Shock(type="cost_spike", target=A, magnitude=30)),
        30,
        14800,
        25,
        -2500,       # 2,75,000 * 1.30 = 3,57,500 leaves 67,500 vs the 70,000 C invoice
        25,
        ["Supplier C invoice"],
    ),
    (
        "verma_late7",
        _plan(shock=Shock(type="customer_delay", target=VERMA, magnitude=7)),
        30,
        14800,
        None,
        6000,        # day 25 after A invoice, before Verma's pushed payment
        25,
        [],
    ),
]


@pytest.mark.parametrize(
    "label,plan,stockout,lost,first_negative,lowest_cash,lowest_day,failed_names",
    CASES,
    ids=[c[0] for c in CASES],
)
def test_oracle(business, label, plan, stockout, lost, first_negative, lowest_cash, lowest_day, failed_names):
    from app.engine.sim import simulate_plan

    result = simulate_plan(business, plan)
    s = result.summary

    assert s["stockout_day"] == stockout, label
    assert s["lost_sales_inr"] == pytest.approx(lost), label
    assert s["first_negative_day"] == first_negative, label
    assert s["lowest_cash_inr"] == pytest.approx(lowest_cash), label
    assert s["lowest_cash_day"] == lowest_day, label
    assert [f["name"] for f in result.details["failed_payments"]] == failed_names, label
