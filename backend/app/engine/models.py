"""Pydantic models for the BizSim engine.

These models are the engine's only vocabulary. The engine never reads the
database directly; callers build a :class:`Business` with
:mod:`app.engine.adapters`. All money is a plain number of Indian rupees; the
field suffix ``_inr`` marks numeric amounts and the text form is formatted with
Indian digit grouping by :func:`app.explain.reasons.format_inr`.

No demo values live here; every number is supplied by the caller.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class Product(BaseModel):
    """A stock-keeping unit.

    Attributes
    ----------
    id, name:
        Stable identifier and display name.
    price_inr:
        Selling price per unit to walk-in customers, in rupees.
    cost_inr:
        Purchase cost per unit, in rupees.
    demand_per_day:
        Average units sold to walk-ins per day (base demand).
    opening_stock:
        Units on hand at the start of day 1.
    supplier:
        Id of the supplier that replenishes this product (``None`` if none).
    """

    id: str
    name: str
    price_inr: float
    cost_inr: float
    demand_per_day: float
    opening_stock: float
    supplier: Optional[str] = None


class Supplier(BaseModel):
    """A supplier the business buys from."""

    id: str
    name: str


class Customer(BaseModel):
    """A customer the business sells to."""

    id: str
    name: str


class Restock(BaseModel):
    """A scheduled inbound delivery with an invoice.

    ``invoice_inr`` is the value of the goods delivered. The invoice **due day
    is fixed at order time** and does not move when the delivery is late.
    """

    supplier: str
    day: int
    items: dict[str, float] = Field(default_factory=dict)
    invoice_inr: float = 0.0
    due_day: int = 0


class Order(BaseModel):
    """A customer order that is delivered on the first day stock allows."""

    id: str
    customer: str
    items: dict[str, float] = Field(default_factory=dict)
    amount_inr: float = 0.0
    target_delivery_day: int = 0
    payment_terms_days: int = 7


class Payable(BaseModel):
    """A standalone amount owed, due on a fixed day."""

    name: str
    amount_inr: float
    due_day: int
    supplier: Optional[str] = None


class AlternativeVendor(BaseModel):
    """The optional replacement distributor used by a switch action."""

    id: str
    name: str
    price_discount_pct: float = 0.0
    advance_pct: float = 50.0
    advance_day: int = 3
    delivery_day: int = 6
    balance_due_days: int = 15


class Business(BaseModel):
    """Everything the engine needs to know about one business.

    The engine is pure: two :class:`Business` objects that compare equal produce
    identical simulations.
    """

    name: str
    cash_inr: float
    fixed_cost_per_day_inr: float = 0.0
    other_supplies_per_day_inr: float = 0.0
    horizon_days: int = 30
    products: list[Product] = Field(default_factory=list)
    suppliers: list[Supplier] = Field(default_factory=list)
    customers: list[Customer] = Field(default_factory=list)
    restocks: list[Restock] = Field(default_factory=list)
    orders: list[Order] = Field(default_factory=list)
    payables: list[Payable] = Field(default_factory=list)
    alternative_vendor: Optional[AlternativeVendor] = None
    # Supplier whose products define the headline "lost sales" metric. The
    # reference oracle scopes lost walk-in sales to the disrupted supply chain.
    primary_supplier: Optional[str] = None

    @property
    def daily_costs_inr(self) -> float:
        """Total fixed + variable daily running cost in rupees."""
        return self.fixed_cost_per_day_inr + self.other_supplies_per_day_inr

    def product(self, product_id: str) -> Product:
        for p in self.products:
            if p.id == product_id:
                return p
        raise KeyError(product_id)

    def supplier_name(self, supplier_id: Optional[str]) -> Optional[str]:
        if supplier_id is None:
            return None
        for s in self.suppliers:
            if s.id == supplier_id:
                return s.name
        return supplier_id

    def customer_name(self, customer_id: Optional[str]) -> Optional[str]:
        if customer_id is None:
            return None
        for c in self.customers:
            if c.id == customer_id:
                return c.name
        return customer_id


# ---------------------------------------------------------------------------
# Scenario / shock models
# ---------------------------------------------------------------------------

ShockType = Literal["supplier_delay", "customer_delay", "cost_spike", "demand_shock"]


class Shock(BaseModel):
    """One disruption applied to the business.

    ``magnitude`` units depend on ``type``:

    * ``supplier_delay`` / ``customer_delay``: days.
    * ``cost_spike``: percent increase on the target supplier's invoices.
    * ``demand_shock``: percent change in walk-in demand.
    """

    type: ShockType
    target: str = ""
    magnitude: float = 0.0
    duration_days: Optional[int] = None


class Plan(BaseModel):
    """A shock plus the preventive actions being compared.

    This is the single configuration object the simulator consumes, so every
    scenario and action runs through one code path.
    """

    shock: Optional[Shock] = None
    invoice_extension_days: int = 0
    invoice_extension_supplier: Optional[str] = None
    payable_extension_days: int = 0
    payable_extension_target: Optional[str] = None
    early_discount_pct: float = 0.0
    discount_customer: Optional[str] = None
    switch_vendor: bool = False
    vendor_fails: bool = False
    demand_multiplier: float = 1.0
    label: str = "do_nothing"

    def shock_type(self) -> str:
        return self.shock.type if self.shock else "none"


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class Assumption(BaseModel):
    """A stated modelling assumption with its source."""

    id: str
    text: str
    value: Optional[float] = None
    unit: Optional[str] = None
    editable: bool = False
    source: Literal["demo_data", "assumed", "user"] = "assumed"


class Event(BaseModel):
    """A structured, causally linked thing that happened on a day."""

    id: str
    day: int
    type: str
    entity: str
    values: dict[str, float | str] = Field(default_factory=dict)
    cause_ids: list[str] = Field(default_factory=list)
    severity: Literal["info", "warning", "critical"] = "info"


class CascadeStep(BaseModel):
    """One step of the standard cascade map."""

    step: str
    status: Literal["triggered", "avoided", "not_reached"]
    day: Optional[int] = None
    title: str
    detail: str


class Explanation(BaseModel):
    """A plain-language reason for one summary metric."""

    metric_id: str
    label: str
    value: float | int | None
    unit: str
    sentence: str
    event_ids: list[str] = Field(default_factory=list)


class RangeCase(BaseModel):
    case: str
    demand_multiplier: float
    metrics: dict[str, float | int | None] = Field(default_factory=dict)


class RangeMetric(BaseModel):
    min: float | int | None = None
    base: float | int | None = None
    max: float | int | None = None
    min_case: Optional[str] = None
    max_case: Optional[str] = None


class Ranges(BaseModel):
    runs: list[RangeCase] = Field(default_factory=list)
    metrics: dict[str, RangeMetric] = Field(default_factory=dict)
    range_note: str = ""


class SimResult(BaseModel):
    """The full result of one simulation run."""

    scenario: dict = Field(default_factory=dict)
    summary: dict = Field(default_factory=dict)
    cascade_chain: list[CascadeStep] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    timeline: dict = Field(default_factory=dict)
    explanations: list[Explanation] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    ranges: Ranges = Field(default_factory=Ranges)
    meta: dict = Field(default_factory=dict)
    # Extra machine-readable detail used by the action comparison layer.
    details: dict = Field(default_factory=dict)


class RiskFactor(BaseModel):
    points: int
    reason: str


class Risk(BaseModel):
    level: Literal["Low", "Medium", "High"]
    score: int
    factors: list[RiskFactor] = Field(default_factory=list)


class ActionResult(BaseModel):
    """A simulation result plus its comparison-to-baseline extras."""

    id: str
    label: str
    result: SimResult
    delta_vs_do_nothing: dict = Field(default_factory=dict)
    tradeoff: str = ""
    affordable: bool = True
    shortfall_inr: float = 0.0
    requires_counterparty_agreement: bool = False
    risk: Risk = Field(default_factory=lambda: Risk(level="Low", score=0))
    suggested: bool = False
    vendor_risk: Optional[dict] = None
    exposure_inr: Optional[float] = None
    vendor_fails_result: Optional[SimResult] = None
