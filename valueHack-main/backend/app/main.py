import os
from typing import Optional

from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session

from .db import create_db_and_tables, get_session
from .engine.actions import compare_actions
from .engine.adapters import business_from_db, business_from_dict
from .engine.analytics import attention_inputs, dependency_shares, stock_cover
from .engine.anomaly import run_full_anomaly_detection
from .engine.cascade import build_plan, resolve_target, simulate
from .engine.csv_loader import (
    CSV_INVALID_FORMAT,
    load_validated_rows_into_db,
    parse_and_validate_csv,
)
from .engine.errors import INVALID_SHOCK, EngineError
from .engine.forecast import generate_business_forecast
from .engine.models import Shock
from .explain.report import generate_report
from .routers.engine import router as engine_router
from .seed import demo_business_dict, seed_demo_data
from .signals.llm import parse_scenario
from .signals.vendor import check_vendor

app = FastAPI(title="BizSim Backend API", version="1.0.0")

# CORS configuration supporting configurable frontend origin
frontend_url = os.getenv("FRONTEND_URL", "").strip()
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)
if not frontend_url:
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(engine_router)


@app.exception_handler(EngineError)
async def engine_error_handler(request, exc: EngineError):
    """Serialize every engine and CSV validation error in the shared {code, message} format."""
    return JSONResponse(status_code=exc.status, content=exc.to_dict())


@app.on_event("startup")
def on_startup():
    seed_demo_data()


def _demo_business():
    """The demo business straight from seed data (no DB round trip needed)."""
    return business_from_dict(demo_business_dict())


@app.get("/health")
def health():
    return {"status": "ok", "ok": True, "version": "1.0", "service": "bizsim-backend"}


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


@app.post("/api/business/load")
async def api_business_load(
    file: UploadFile = File(...),
    table_type: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Accept and validate CSV business data and load it into SQLite database."""
    try:
        content_bytes = await file.read()
        try:
            content_str = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content_str = content_bytes.decode("latin-1")
    except Exception as exc:
        raise EngineError(CSV_INVALID_FORMAT, f"Failed to read CSV payload: {exc}")

    table, rows = parse_and_validate_csv(
        content=content_str,
        table_type=table_type,
        session=session,
    )
    loaded_count = load_validated_rows_into_db(table_type=table, rows=rows, session=session)

    return {
        "status": "success",
        "table": table,
        "rows_loaded": loaded_count,
        "message": f"Successfully loaded and validated {loaded_count} {table} records.",
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
    return check_vendor(query=params.name or params.gstin or params.pan, gstin=params.gstin or None, pan=params.pan or None)


from .signals.bills import parse_bill_file


@app.post("/api/bill/scan")
async def api_bill_scan(file: UploadFile = File(...)):
    try:
        content_bytes = await file.read()
        return parse_bill_file(content_bytes, filename=file.filename or "invoice.pdf")
    except Exception as exc:
        raise EngineError(CSV_INVALID_FORMAT, f"Failed to parse bill: {exc}")


class BillConfirmParams(BaseModel):
    supplier: str
    amount: float
    due_day: int = 25
    invoice_number: str = ""


@app.post("/api/bill/confirm")
def api_bill_confirm(params: BillConfirmParams, session: Session = Depends(get_session)):
    payable = Payable(
        name=f"Invoice {params.invoice_number or params.supplier}",
        amount=params.amount,
        due_day=params.due_day,
        supplier_name=params.supplier,
        business_id=1,
    )
    session.add(payable)
    session.commit()
    return {"status": "success", "message": f"Payable of ₹{params.amount:,.0f} scheduled for Day {params.due_day}."}


@app.get("/api/attention")
def api_attention(session: Session = Depends(get_session)):
    """Aggregate attention items: dynamically detected anomalies and engine stock/supplier alerts."""
    try:
        business = business_from_db(session)
    except Exception:
        business = _demo_business()

    engine_items = attention_inputs(business)
    anomaly_data = run_full_anomaly_detection()
    anomaly_items = anomaly_data.get("anomalies", [])

    unified_items = []
    item_id = 1

    # Add anomaly items first (high priority warnings)
    for a in anomaly_items:
        icon = "alert-circle"
        if a["metric"] == "cost":
            icon = "trending-up"
        elif a["metric"] == "sales":
            icon = "trending-down"
        elif a["metric"] == "bill":
            icon = "file-text"

        unified_items.append(
            {
                "id": item_id,
                "text": a["reason"],
                "title": a.get("reason", "").split(":")[0],
                "icon": icon,
                "type": "anomaly",
                "kind": f"anomaly_{a['metric']}",
                "metric": a["metric"],
                "severity": a["severity"],
                "date": a.get("date"),
                "value": a.get("value"),
                "expected_value": a.get("expected_value"),
                "evidence": a["reason"],
            }
        )
        item_id += 1

    # Add engine operational alerts
    for e in engine_items:
        icon = "alert-circle"
        if e["kind"] == "low_cover":
            icon = "box"
        elif e["kind"] == "supplier_concentration":
            icon = "pie-chart"
        elif e["kind"] == "payable_thin_cash":
            icon = "clock"

        unified_items.append(
            {
                "id": item_id,
                "text": e["evidence"],
                "title": f"{e['entity']} {e['kind'].replace('_', ' ').title()}",
                "icon": icon,
                "type": "business",
                "kind": e["kind"],
                "entity": e["entity"],
                "severity": e["severity"],
                "day": e.get("day"),
                "evidence": e["evidence"],
            }
        )
        item_id += 1

    return unified_items


@app.get("/api/forecast")
def api_forecast(days: int = 30, holdout: int = 14):
    """30-day product demand forecast with Holt-Winters / seasonal fallback and 14-day holdout MAPE."""
    return generate_business_forecast(forecast_days=days, holdout_days=holdout)


@app.get("/api/anomalies")
def api_anomalies():
    """Detect anomalies across sales, costs, bills, and stock."""
    return run_full_anomaly_detection()


@app.get("/api/report")
def api_report():
    buf = generate_report()
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=report.pdf"},
    )
