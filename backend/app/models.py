from typing import Optional
from sqlmodel import Field, SQLModel


class Business(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    cash: float
    fixed_cost: float
    other_supplies: float


class Supplier(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    business_id: int = 1


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    cost: float
    demand_per_day: float
    opening_stock: int
    supplier_name: Optional[str] = None
    business_id: int = 1


class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    business_id: int = 1


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: Optional[str] = None
    customer_name: str
    items: str = ""
    amount: float
    target_delivery_day: int
    payment_terms_days: int = 7
    business_id: int = 1


class Receivable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    amount: float
    due_day: int
    customer_name: Optional[str] = None
    business_id: int = 1


class Payable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    amount: float
    due_day: int
    supplier_name: Optional[str] = None
    business_id: int = 1


class Bill(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bill_number: Optional[str] = None
    supplier_name: str
    amount: float
    date: str  # YYYY-MM-DD
    due_date: str  # YYYY-MM-DD
    status: str = "pending"
    business_id: int = 1


class VendorCheck(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    score: Optional[int] = None
    risk_level: Optional[str] = None
    business_id: int = 1


class Scenario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    scenario_type: str
    target: str
    magnitude: float
    duration_days: Optional[int] = None
    business_id: int = 1


class DailySale(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str  # YYYY-MM-DD
    day_index: int
    product_name: str
    units_sold: float
    unit_price: float
    unit_cost: float
    revenue: float
    cost: float
    business_id: int = 1
