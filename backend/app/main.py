from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session

from .db import create_db_and_tables, get_session
from .engine.actions import compare_actions
from .engine.adapters import business_from_db, business_from_dict
from .engine.analytics import attention_inputs, dependency_shares, stock_cover
from .engine.cascade import build_plan, resolve_target, simulate
from .engine.errors import INVALID_SHOCK, EngineError
from .engine.models import Shock
from .routers.engine import router as engine_router
from .seed import demo_business_dict, seed_demo_data
from .signals.llm import parse_scenario
from .signals.vendor import check_vendor
from .explain.report import generate_report

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(engine_router)


@app.exception_handler(EngineError)
async def engine_error_handler(request, exc: EngineError):
    """Serialize every engine error in the shared ``{code, message}`` format."""
    return JSONResponse(status_code=exc.status, content=exc.to_dict())


@app.on_event("startup")
def on_startup():
    seed_demo_data()


def _demo_business():
    """The demo business straight from seed data (no DB round trip needed)."""
    return business_from_dict(demo_business_dict())


@app.get("/health")
def health():
    return {"ok": True, "version": "1.0"}


@app.get("/api/business")
def get_business(session: Session = Depends(get_session)):
    try:
        business = business_from_db(session)
    except Exception:
        business = _demo_business()
    return {
        "name": business.name,
        "cash": business.cash_inr,
        "analytics": {
            "dependency_shares": dependency_shares(business),
            "stock_cover": stock_cover(business),
            "attention_inputs": attention_inputs(business),
        },
    }


class ScenarioShock(BaseModel):
    type: str = "supplier_delay"
    target: str = ""
    magnitude: float = 0.0
    duration_days: int | None = None


class CascadeParams(BaseModel):
    delay: int = 0
    horizon: int = 30
    ext_a: int = 0
    ext_c: int = 0
    early_discount: float = 0.0
    alt_supplier: bool = False
    alt_fails: bool = False
    cost_spike_pct: float = 0.0
    customer_late_days: int = 0
    demand_band_pct: float = 20.0
    scenario: ScenarioShock | None = None


@app.post("/api/simulate/cascade")
def api_simulate_cascade(params: CascadeParams):
    business = _demo_business().model_copy(update={"horizon_days": params.horizon})
    shock = None
    if params.scenario is not None:
        if params.scenario.type not in ("supplier_delay", "customer_delay", "cost_spike", "demand_shock"):
            raise EngineError(INVALID_SHOCK, f"Unknown scenario type '{params.scenario.type}'.")
        shock = Shock(
            type=params.scenario.type,
            target=params.scenario.target,
            magnitude=params.scenario.magnitude,
            duration_days=params.scenario.duration_days,
        )
        shock = resolve_target(business, shock)
    plan = build_plan(
        business,
        delay=params.delay,
        ext_a=params.ext_a,
        ext_c=params.ext_c,
        early_discount=params.early_discount,
        alt_supplier=params.alt_supplier,
        alt_fails=params.alt_fails,
        cost_spike_pct=params.cost_spike_pct,
        customer_late_days=params.customer_late_days,
        shock=shock,
    )
    return simulate(
        business=business,
        plan=plan,
        horizon=params.horizon,
        demand_band_pct=params.demand_band_pct,
    )


class ActionParams(BaseModel):
    delay: int


@app.post("/api/actions/compare")
def api_compare_actions(params: ActionParams):
    return compare_actions(params.delay)


class ScenarioParams(BaseModel):
    text: str


@app.post("/api/scenario/parse")
def api_parse_scenario(params: ScenarioParams):
    return parse_scenario(params.text)


class VendorParams(BaseModel):
    name: str = ""
    gstin: str = ""
    pan: str = ""


@app.post("/api/vendor/check")
def api_vendor_check(params: VendorParams):
    return check_vendor(params.name or params.gstin)


@app.post("/api/bill/scan")
def api_bill_scan(file: UploadFile = File(...)):
    return {
        "supplier": "Sample Supplier",
        "items": [{"name": "Sample Item", "qty": 1, "unit_price": 100, "tax_rate": 18}],
        "due_date": "2024-12-31",
    }


@app.get("/api/attention")
def api_attention():
    return [
        {"id": 1, "text": "Supplier A delay risk", "icon": "alert-circle"},
        {"id": 2, "text": "Cash flow dip expected day 23", "icon": "trending-down"},
        {"id": 3, "text": "Supplier C payment due soon", "icon": "clock"},
        {"id": 4, "text": "Verma Contractors order pending", "icon": "box"},
        {"id": 5, "text": "High concentration on Supplier A", "icon": "pie-chart"},
    ]


@app.get("/api/forecast")
def api_forecast():
    return {"forecast": [], "mape": 0.05}


@app.get("/api/anomalies")
def api_anomalies():
    return []


@app.get("/api/report")
def api_report():
    buf = generate_report()
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=report.pdf"})
