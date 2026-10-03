"""Adapters that build a :class:`~app.engine.models.Business` from other sources.

The engine never opens the database itself. ``business_from_dict`` builds a
business from a plain dict (used by tests and CSV loaders) and
``business_from_db`` reads the SQLModel rows and merges the demo schedule from
seed data.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlmodel import Session

from .models import (
    AlternativeVendor,
    Business,
    Customer,
    Order,
    Payable,
    Product,
    Restock,
    Supplier,
)


def business_from_dict(data: dict[str, Any]) -> Business:
    """Validate a plain dict into a :class:`Business`."""
    return Business.model_validate(data)


def _slug(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def business_from_db(session: Session, schedule: Optional[dict[str, Any]] = None) -> Business:
    """Build a business from SQLModel rows.

    The database currently stores the business, its products, suppliers and
    customers. Scheduled restocks, orders and payables are demo configuration
    and are merged from ``schedule`` (defaulting to the demo seed) so that no
    demo value lives in engine code.
    """
    # Imported lazily so importing the engine never has a seed-data side effect.
    from ..seed import demo_business_dict

    from ..models import Business as BusinessRow
    from ..models import Customer as CustomerRow
    from ..models import Product as ProductRow
    from ..models import Supplier as SupplierRow

    sched = schedule or demo_business_dict()

    row = session.query(BusinessRow).first()
    if row is None:
        raise ValueError("No business row found; seed the database first.")

    suppliers = [Supplier(id=_slug(s.name), name=s.name) for s in session.query(SupplierRow).all()]
    supplier_by_id = {s.id: s for s in suppliers}

    # The demo schedule tells us which supplier replenishes which product.
    supplier_for: dict[str, str] = {}
    for p in sched.get("products", []):
        supplier_for[_slug(p["name"])] = p.get("supplier")

    products = [
        Product(
            id=_slug(p.name),
            name=p.name,
            price_inr=p.price,
            cost_inr=p.cost,
            demand_per_day=p.demand_per_day,
            opening_stock=p.opening_stock,
            supplier=supplier_for.get(_slug(p.name)),
        )
        for p in session.query(ProductRow).all()
    ]

    customers = [Customer(id=_slug(c.name), name=c.name) for c in session.query(CustomerRow).all()]

    return Business(
        name=row.name,
        cash_inr=row.cash,
        fixed_cost_per_day_inr=row.fixed_cost,
        other_supplies_per_day_inr=row.other_supplies,
        horizon_days=sched.get("horizon_days", 30),
        products=products,
        suppliers=suppliers,
        customers=customers,
        restocks=[Restock.model_validate(r) for r in sched.get("restocks", [])],
        orders=[Order.model_validate(o) for o in sched.get("orders", [])],
        payables=[Payable.model_validate(p) for p in sched.get("payables", [])],
        alternative_vendor=(
            AlternativeVendor.model_validate(sched["alternative_vendor"])
            if sched.get("alternative_vendor")
            else None
        ),
        primary_supplier=sched.get("primary_supplier"),
    )
