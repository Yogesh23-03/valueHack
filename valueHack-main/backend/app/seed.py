"""Seed data for the BizSim demo business.

Demo numbers live **only** here and in test fixtures. Engine modules receive a
``Business`` object and never contain hard-coded demo values.
"""

from __future__ import annotations

from sqlmodel import Session

from .db import create_db_and_tables, engine
from .models import Business as BusinessRow
from .models import Customer, Product, Supplier

# The reference demo business, expressed as a plain dict the engine adapters
# understand. Amounts are in rupees, horizon is 30 days.
DEMO_BUSINESS: dict = {
    "name": "Sharma Hardware and Electricals",
    "cash_inr": 50000,
    "fixed_cost_per_day_inr": 3000,
    "other_supplies_per_day_inr": 1800,
    "horizon_days": 30,
    "primary_supplier": "sup_a",
    "suppliers": [
        {"id": "sup_a", "name": "Supplier A"},
        {"id": "sup_c", "name": "Supplier C"},
        {"id": "new_dist", "name": "New Distributor"},
    ],
    "customers": [
        {"id": "verma", "name": "Verma Contractors"},
    ],
    "products": [
        {
            "id": "fans",
            "name": "Fans",
            "price_inr": 1900,
            "cost_inr": 1400,
            "demand_per_day": 4,
            "opening_stock": 36,
            "supplier": "sup_a",
        },
        {
            "id": "wiring",
            "name": "Wiring coils",
            "price_inr": 1200,
            "cost_inr": 900,
            "demand_per_day": 6,
            "opening_stock": 54,
            "supplier": "sup_a",
        },
        {
            "id": "switches",
            "name": "Switches",
            "price_inr": 170,
            "cost_inr": 95,
            "demand_per_day": 15,
            "opening_stock": 300,
            "supplier": "sup_c",
        },
    ],
    # Supplier A restock: 100 fans + 150 coils arriving day 8.
    # Invoice = 100*1400 + 150*900 = 2,75,000, due day 23.
    "restocks": [
        {
            "supplier": "sup_a",
            "day": 8,
            "items": {"fans": 100, "wiring": 150},
            "invoice_inr": 275000,
            "due_day": 23,
        }
    ],
    # Verma Contractors: 20 fans + 30 coils = 74,000; target delivery day 12;
    # pays 7 days after delivery.
    "orders": [
        {
            "id": "verma_order",
            "customer": "verma",
            "items": {"fans": 20, "wiring": 30},
            "amount_inr": 74000,
            "target_delivery_day": 12,
            "payment_terms_days": 7,
        }
    ],
    "payables": [
        {"name": "Supplier C invoice", "supplier": "sup_c", "amount_inr": 70000, "due_day": 25}
    ],
    "alternative_vendor": {
        "id": "new_dist",
        "name": "New Distributor",
        "price_discount_pct": 15.0,
        "advance_pct": 50.0,
        "advance_day": 3,
        "delivery_day": 6,
        "balance_due_days": 15,
    },
}


def demo_business_dict() -> dict:
    """Return a deep-ish copy of the reference demo business dict."""
    import copy

    return copy.deepcopy(DEMO_BUSINESS)


def seed_demo_data() -> None:
    """Create tables and insert the demo business rows if they are absent."""
    create_db_and_tables()
    with Session(engine) as session:
        if session.query(BusinessRow).first():
            return

        b = BusinessRow(
            name="Sharma Hardware and Electricals",
            cash=50000,
            fixed_cost=3000,
            other_supplies=1800,
        )
        session.add(b)
        session.commit()

        p1 = Product(name="fans", price=1900, cost=1400, demand_per_day=4, opening_stock=36, business_id=b.id)
        p2 = Product(name="wiring", price=1200, cost=900, demand_per_day=6, opening_stock=54, business_id=b.id)
        p3 = Product(name="switches", price=170, cost=95, demand_per_day=15, opening_stock=300, business_id=b.id)
        session.add_all([p1, p2, p3])

        s1 = Supplier(name="Supplier A", business_id=b.id)
        s2 = Supplier(name="Supplier C", business_id=b.id)
        s3 = Supplier(name="New Distributor", business_id=b.id)
        session.add_all([s1, s2, s3])

        c1 = Customer(name="Verma Contractors", business_id=b.id)
        session.add(c1)

        session.commit()


if __name__ == "__main__":
    seed_demo_data()
