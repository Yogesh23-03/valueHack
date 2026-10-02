from sqlmodel import SQLModel, Field
from typing import Optional

class Business(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    cash: float
    fixed_cost: float
    other_supplies: float

class Supplier(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    business_id: int

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    cost: float
    demand_per_day: float
    opening_stock: int
    business_id: int

class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    business_id: int
