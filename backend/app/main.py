from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from .db import create_db_and_tables
from .seed import seed_demo_data
from .engine.cascade import simulate
from .engine.actions import compare_actions
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

@app.on_event("startup")
def on_startup():
    seed_demo_data()

@app.get("/health")
def health():
    return {"ok": True, "version": "1.0"}

@app.get("/api/business")
def get_business():
    return {"name": "Sharma Hardware and Electricals", "cash": 50000}

class CascadeParams(BaseModel):
    delay: int = 0
    horizon: int = 30
    ext_a: int = 0
    ext_c: int = 0
    early_discount: float = 0.0
    alt_supplier: bool = False
    cost_spike_pct: float = 0.0
    customer_late_days: int = 0

@app.post("/api/simulate/cascade")
def api_simulate_cascade(params: CascadeParams):
    return simulate(**params.dict())

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
    return {"supplier": "Sample Supplier", "items": [{"name": "Sample Item", "qty": 1, "unit_price": 100, "tax_rate": 18}], "due_date": "2024-12-31"}

@app.get("/api/attention")
def api_attention():
    return [
        {"id": 1, "text": "Supplier A delay risk", "icon": "alert-circle"},
        {"id": 2, "text": "Cash flow dip expected day 23", "icon": "trending-down"},
        {"id": 3, "text": "Supplier C payment due soon", "icon": "clock"},
        {"id": 4, "text": "Verma Contractors order pending", "icon": "box"},
        {"id": 5, "text": "High concentration on Supplier A", "icon": "pie-chart"}
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
