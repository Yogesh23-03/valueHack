"""Synthetic data generator for BizSim demo business: Sharma Hardware and Electricals.

Generates 90 days of daily sales with weekly seasonality and planted anomalies:
1. One unusually high-cost day (Day 45, 2025-12-17)
2. One unusually low-sales day (Day 70, 2026-01-11)
3. One overpriced bill (Day 55, 2025-12-27)

Reproducible with a fixed random seed (default: 42).
All generated numbers are labeled as synthetic / demo data.
"""

from __future__ import annotations

import datetime
import random
from typing import Any, Optional


DEMO_BUSINESS = {
    "name": "Sharma Hardware and Electricals",
    "cash": 50000.0,
    "fixed_cost": 3000.0,
    "other_supplies": 1800.0,
}

DEMO_SUPPLIERS = [
    {"id": 1, "name": "Supplier A", "slug": "supplier_a"},
    {"id": 2, "name": "Supplier C", "slug": "supplier_c"},
    {"id": 3, "name": "New Distributor", "slug": "new_distributor"},
]

DEMO_PRODUCTS = [
    {
        "id": 1,
        "name": "fans",
        "price": 1900.0,
        "cost": 1400.0,
        "demand_per_day": 4.0,
        "opening_stock": 36,
        "supplier_name": "Supplier A",
    },
    {
        "id": 2,
        "name": "wiring",
        "price": 1200.0,
        "cost": 900.0,
        "demand_per_day": 6.0,
        "opening_stock": 54,
        "supplier_name": "Supplier A",
    },
    {
        "id": 3,
        "name": "switches",
        "price": 170.0,
        "cost": 95.0,
        "demand_per_day": 15.0,
        "opening_stock": 300,
        "supplier_name": "Supplier C",
    },
]

DEMO_CUSTOMERS = [
    {"id": 1, "name": "Verma Contractors", "slug": "verma_contractors"},
]

DEMO_ORDERS = [
    {
        "id": 1,
        "order_id": "ORD-VERMA-01",
        "customer_name": "Verma Contractors",
        "items": "fans:20,wiring:30",
        "amount": 74000.0,
        "target_delivery_day": 12,
        "payment_terms_days": 7,
    }
]

DEMO_PAYABLES = [
    {
        "id": 1,
        "name": "Supplier A invoice",
        "amount": 275000.0,
        "due_day": 23,
        "supplier_name": "Supplier A",
    },
    {
        "id": 2,
        "name": "Supplier C",
        "amount": 70000.0,
        "due_day": 25,
        "supplier_name": "Supplier C",
    },
]

DEMO_RECEIVABLES = [
    {
        "id": 1,
        "name": "Verma Contractors payment",
        "amount": 74000.0,
        "due_day": 19,
        "customer_name": "Verma Contractors",
    }
]

# Weekly seasonality factors (Monday=0 to Sunday=6)
# Retail electrical and hardware shops tend to be steady on weekdays, peak on Saturdays, slower on Sundays.
WEEKLY_SEASONALITY = [1.0, 1.05, 0.95, 1.0, 1.1, 1.25, 0.65]

# Planted anomaly specifications
PLANTED_ANOMALIES = [
    {
        "day_index": 45,
        "date": "2025-12-17",
        "metric": "cost",
        "product": "all",
        "type": "high_cost",
        "observed_value": 52800.0,
        "expected_value": 17800.0,
        "severity": "high",
        "reason": "Unusually high daily cost (₹52,800 vs expected ~₹17,800) due to emergency equipment overhaul",
    },
    {
        "day_index": 70,
        "date": "2026-01-11",
        "metric": "sales",
        "product": "all",
        "type": "low_sales",
        "observed_value": 0.0,
        "expected_value": 17350.0,
        "severity": "high",
        "reason": "Unusually low sales (₹0 across all products vs expected ~₹17,350) due to city-wide transport strike",
    },
    {
        "day_index": 55,
        "date": "2025-12-27",
        "metric": "bill",
        "supplier": "Supplier C",
        "type": "overpriced_bill",
        "observed_value": 125000.0,
        "expected_value": 70000.0,
        "severity": "high",
        "reason": "Overpriced supplier invoice (₹125,000 vs historical expectation ₹70,000 from Supplier C)",
    },
]


def generate_synthetic_sales(
    days: int = 90,
    seed: int = 42,
    start_date: Optional[datetime.date] = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate reproducible daily sales for 90 days with planted anomalies.

    Parameters
    ----------
    days:
        Number of historical days to generate (default: 90).
    seed:
        Fixed random seed for deterministic reproduction (default: 42).
    start_date:
        Starting date for day 1. If None, ends on 2026-01-31.

    Returns
    -------
    (daily_sales_records, daily_summary_records, bills_records)
    """
    rng = random.Random(seed)

    if start_date is None:
        # Default: 90 days ending on 2026-01-31
        end_date = datetime.date(2026, 1, 31)
        start_date = end_date - datetime.timedelta(days=days - 1)

    daily_sales: list[dict[str, Any]] = []
    daily_summaries: list[dict[str, Any]] = []
    bills: list[dict[str, Any]] = []

    # Map planted anomalies by day index
    planted_by_day: dict[int, list[dict[str, Any]]] = {}
    for pa in PLANTED_ANOMALIES:
        planted_by_day.setdefault(pa["day_index"], []).append(pa)

    current_stock = {p["name"]: p["opening_stock"] for p in DEMO_PRODUCTS}

    for d in range(1, days + 1):
        curr_date = start_date + datetime.timedelta(days=d - 1)
        date_str = curr_date.isoformat()
        weekday = curr_date.weekday()
        season_factor = WEEKLY_SEASONALITY[weekday]

        day_anomalies = planted_by_day.get(d, [])
        is_low_sales_day = any(a["type"] == "low_sales" for a in day_anomalies)
        is_high_cost_day = any(a["type"] == "high_cost" for a in day_anomalies)
        is_overpriced_bill_day = any(a["type"] == "overpriced_bill" for a in day_anomalies)

        day_total_rev = 0.0
        day_total_cost = 0.0
        day_product_sales: dict[str, float] = {}

        for prod in DEMO_PRODUCTS:
            pname = prod["name"]
            price = prod["price"]
            cost = prod["cost"]
            base_demand = prod["demand_per_day"]

            if is_low_sales_day:
                units = 0.0
            else:
                # Add normal noise scaled to base demand (approx +- 15%)
                noise = rng.gauss(0.0, 0.15 * base_demand)
                units = max(0.0, round(base_demand * season_factor + noise))

            rev = units * price
            cogs = units * cost

            day_total_rev += rev
            day_total_cost += cogs
            day_product_sales[pname] = units

            daily_sales.append(
                {
                    "day_index": d,
                    "date": date_str,
                    "product_name": pname,
                    "units_sold": units,
                    "unit_price": price,
                    "unit_cost": cost,
                    "revenue": rev,
                    "cost": cogs,
                    "is_synthetic": True,
                }
            )

        # Operating expenses: fixed (3000) + other supplies (1800)
        daily_opex = DEMO_BUSINESS["fixed_cost"] + DEMO_BUSINESS["other_supplies"]
        if is_high_cost_day:
            # Planted spike: add emergency overhaul expense of ₹35,000
            total_day_cost = day_total_cost + daily_opex + 35000.0
        else:
            total_day_cost = day_total_cost + daily_opex

        daily_summaries.append(
            {
                "day_index": d,
                "date": date_str,
                "revenue": day_total_rev,
                "cogs": day_total_cost,
                "opex": daily_opex if not is_high_cost_day else daily_opex + 35000.0,
                "total_cost": total_day_cost,
                "net_cash_flow": day_total_rev - total_day_cost,
                "sales_by_product": day_product_sales,
                "is_synthetic": True,
            }
        )

        # Generate regular and planted bills
        if d == 15 or d == 40 or d == 65:
            # Regular standard bill from Supplier A
            bills.append(
                {
                    "bill_number": f"INV-A-{d:03d}",
                    "supplier_name": "Supplier A",
                    "amount": 275000.0,
                    "date": date_str,
                    "due_date": (curr_date + datetime.timedelta(days=15)).isoformat(),
                    "status": "paid",
                    "is_synthetic": True,
                }
            )
        elif d == 25 or d == 80:
            # Regular bill from Supplier C
            bills.append(
                {
                    "bill_number": f"INV-C-{d:03d}",
                    "supplier_name": "Supplier C",
                    "amount": 70000.0,
                    "date": date_str,
                    "due_date": (curr_date + datetime.timedelta(days=15)).isoformat(),
                    "status": "paid",
                    "is_synthetic": True,
                }
            )
        elif is_overpriced_bill_day:
            # Planted overpriced bill on Day 55
            bills.append(
                {
                    "bill_number": "INV-C-ANOMALY-055",
                    "supplier_name": "Supplier C",
                    "amount": 125000.0,
                    "date": date_str,
                    "due_date": (curr_date + datetime.timedelta(days=15)).isoformat(),
                    "status": "disputed",
                    "is_synthetic": True,
                    "is_anomaly": True,
                    "anomaly_reason": "Price 78% higher than standard ₹70,000 contract rate",
                }
            )

    return daily_sales, daily_summaries, bills


def generate_full_demo_dataset(seed: int = 42) -> dict[str, Any]:
    """Generate the complete synthetic Sharma Hardware dataset."""
    daily_sales, daily_summaries, bills = generate_synthetic_sales(days=90, seed=seed)

    return {
        "business": DEMO_BUSINESS,
        "suppliers": DEMO_SUPPLIERS,
        "products": DEMO_PRODUCTS,
        "customers": DEMO_CUSTOMERS,
        "orders": DEMO_ORDERS,
        "payables": DEMO_PAYABLES,
        "receivables": DEMO_RECEIVABLES,
        "bills": bills,
        "daily_sales": daily_sales,
        "daily_summaries": daily_summaries,
        "planted_anomalies": PLANTED_ANOMALIES,
        "is_synthetic": True,
        "seed": seed,
    }


def seed_database_with_synthetic_data(session: Any, seed: int = 42) -> None:
    """Populate database tables with synthetic 90-day sales and business data."""
    from ..models import (
        Bill as BillRow,
        Business as BusinessRow,
        Customer as CustomerRow,
        DailySale as DailySaleRow,
        Order as OrderRow,
        Payable as PayableRow,
        Product as ProductRow,
        Receivable as ReceivableRow,
        Supplier as SupplierRow,
    )

    data = generate_full_demo_dataset(seed=seed)

    # Ensure Business exists
    b_row = session.query(BusinessRow).first()
    if not b_row:
        b_row = BusinessRow(
            name=DEMO_BUSINESS["name"],
            cash=DEMO_BUSINESS["cash"],
            fixed_cost=DEMO_BUSINESS["fixed_cost"],
            other_supplies=DEMO_BUSINESS["other_supplies"],
        )
        session.add(b_row)
        session.commit()
        session.refresh(b_row)

    b_id = b_row.id or 1

    # Populate suppliers if empty
    if not session.query(SupplierRow).first():
        for s in DEMO_SUPPLIERS:
            session.add(SupplierRow(name=s["name"], business_id=b_id))
        session.commit()

    # Populate products if empty
    if not session.query(ProductRow).first():
        for p in DEMO_PRODUCTS:
            session.add(
                ProductRow(
                    name=p["name"],
                    price=p["price"],
                    cost=p["cost"],
                    demand_per_day=p["demand_per_day"],
                    opening_stock=p["opening_stock"],
                    supplier_name=p["supplier_name"],
                    business_id=b_id,
                )
            )
        session.commit()

    # Populate customers if empty
    if not session.query(CustomerRow).first():
        for c in DEMO_CUSTOMERS:
            session.add(CustomerRow(name=c["name"], business_id=b_id))
        session.commit()

    # Populate orders if empty
    if not session.query(OrderRow).first():
        for o in DEMO_ORDERS:
            session.add(
                OrderRow(
                    order_id=o["order_id"],
                    customer_name=o["customer_name"],
                    items=o["items"],
                    amount=o["amount"],
                    target_delivery_day=o["target_delivery_day"],
                    payment_terms_days=o["payment_terms_days"],
                    business_id=b_id,
                )
            )
        session.commit()

    # Populate payables if empty
    if not session.query(PayableRow).first():
        for p in DEMO_PAYABLES:
            session.add(
                PayableRow(
                    name=p["name"],
                    amount=p["amount"],
                    due_day=p["due_day"],
                    supplier_name=p["supplier_name"],
                    business_id=b_id,
                )
            )
        session.commit()

    # Populate receivables if empty
    if not session.query(ReceivableRow).first():
        for r in DEMO_RECEIVABLES:
            session.add(
                ReceivableRow(
                    name=r["name"],
                    amount=r["amount"],
                    due_day=r["due_day"],
                    customer_name=r["customer_name"],
                    business_id=b_id,
                )
            )
        session.commit()

    # Populate bills if empty
    if not session.query(BillRow).first():
        for b in data["bills"]:
            session.add(
                BillRow(
                    bill_number=b["bill_number"],
                    supplier_name=b["supplier_name"],
                    amount=b["amount"],
                    date=b["date"],
                    due_date=b["due_date"],
                    status=b["status"],
                    business_id=b_id,
                )
            )
        session.commit()

    # Populate daily sales if empty
    if not session.query(DailySaleRow).first():
        for s in data["daily_sales"]:
            session.add(
                DailySaleRow(
                    date=s["date"],
                    day_index=s["day_index"],
                    product_name=s["product_name"],
                    units_sold=s["units_sold"],
                    unit_price=s["unit_price"],
                    unit_cost=s["unit_cost"],
                    revenue=s["revenue"],
                    cost=s["cost"],
                    business_id=b_id,
                )
            )
        session.commit()


if __name__ == "__main__":
    dataset = generate_full_demo_dataset()
    print(f"Generated {len(dataset['daily_sales'])} product sales records across 90 days.")
    print(f"Planted anomalies: {len(dataset['planted_anomalies'])}")
    for a in dataset["planted_anomalies"]:
        print(f" - [{a['metric'].upper()}] {a['date']} (Day {a['day_index']}): {a['reason']}")
