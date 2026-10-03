import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

backend_reqs = """
fastapi
uvicorn[standard]
pydantic
sqlmodel
pandas
numpy
networkx
scikit-learn
statsmodels
google-generativeai
pdf2image
Pillow
reportlab
python-multipart
"""

backend_env = """
GEMINI_API_KEY=your_key_here
"""

models_py = """
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
"""

db_py = """
from sqlmodel import SQLModel, create_engine, Session

sqlite_file_name = "bizsim.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
"""

seed_py = """
from sqlmodel import Session
from .db import engine, create_db_and_tables
from .models import Business, Supplier, Product, Customer

def seed_demo_data():
    create_db_and_tables()
    with Session(engine) as session:
        if session.query(Business).first():
            return
        
        b = Business(name="Sharma Hardware and Electricals", cash=50000, fixed_cost=3000, other_supplies=1800)
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
"""

cascade_py = """
def simulate(delay=0, horizon=30, start_cash=50000, ext_a=0, ext_c=0, early_discount=0.0, alt_supplier=False, alt_fails=False, cost_spike_pct=0.0, customer_late_days=0) -> dict:
    stock = {"fans": 36, "wiring": 54, "switches": 300}
    demand = {"fans": 4, "wiring": 6, "switches": 15}
    price = {"fans": 1900, "wiring": 1200, "switches": 170}
    
    cash = start_cash
    fixed_cost = 3000 + 1800
    
    # Supplier A restock
    restock_day = 8 + delay
    if alt_supplier and not alt_fails:
        restock_day = 8 # assumed fast
    elif alt_supplier and alt_fails:
        restock_day = 999
        
    sup_a_due = 23 + ext_a
    sup_a_amount = 275000 * (1 - early_discount)
    if early_discount > 0:
        sup_a_due = 10
        
    # Supplier C
    sup_c_due = 25 + ext_c
    sup_c_amount = 70000
    
    # Customer Verma
    verma_qty = {"fans": 20, "wiring": 30}
    verma_amount = 20*1900 + 30*1200 # 74000
    
    stockout_day = None
    first_negative_day = None
    min_cash = cash
    failed = []
    delivered = False
    verma_delivery_day = None
    events = []
    
    cash_timeline = []
    stock_timeline = []
    
    for day in range(1, horizon + 1):
        # Restock
        if day == restock_day:
            stock["fans"] += 100
            stock["wiring"] += 150
            events.append({"day": day, "text": "Restock arrived"})
            
        # Deliver Verma
        if not delivered:
            if stock["fans"] >= verma_qty["fans"] and stock["wiring"] >= verma_qty["wiring"]:
                stock["fans"] -= verma_qty["fans"]
                stock["wiring"] -= verma_qty["wiring"]
                delivered = True
                verma_delivery_day = day
                events.append({"day": day, "text": "Delivered to Verma"})
                
        # Daily sales
        for item in ["fans", "wiring", "switches"]:
            if stock[item] >= demand[item]:
                stock[item] -= demand[item]
                cash += demand[item] * price[item]
            else:
                cash += stock[item] * price[item]
                stock[item] = 0
                if stockout_day is None:
                    stockout_day = day
                    events.append({"day": day, "text": f"Stockout on {item}"})
                    
        cash -= fixed_cost
        
        # Receivables
        if delivered and day == verma_delivery_day + 7 + customer_late_days:
            cash += verma_amount
            events.append({"day": day, "text": "Verma paid"})
            
        # Payables
        if day == sup_a_due:
            if cash >= sup_a_amount:
                cash -= sup_a_amount
            else:
                failed.append({"name": "Supplier A", "day": day})
                
        if day == sup_c_due:
            if cash >= sup_c_amount:
                cash -= sup_c_amount
            else:
                failed.append({"name": "Supplier C", "day": day})
                
        if cash < 0 and first_negative_day is None:
            first_negative_day = day
            events.append({"day": day, "text": "Cash went negative"})
            
        if cash < min_cash:
            min_cash = cash
            
        cash_timeline.append(cash)
        stock_timeline.append(stock.copy())
        
    return {
        "stockout": stockout_day,
        "lost_rev": 0,
        "first_negative_day": first_negative_day,
        "min_cash": min_cash,
        "min_day": 0,
        "failed": failed,
        "delivered": delivered,
        "end_cash": cash,
        "cash_timeline": cash_timeline,
        "stock_timeline": stock_timeline,
        "events": events
    }
"""

actions_py = """
from .cascade import simulate

def compare_actions(delay: int):
    return {
        "do_nothing": simulate(delay=delay),
        "ask_extension": simulate(delay=delay, ext_a=15, ext_c=15),
        "early_discount": simulate(delay=delay, early_discount=0.02),
        "switch_vendor": simulate(delay=delay, alt_supplier=True, alt_fails=True),
        "combined": simulate(delay=delay, ext_c=15, early_discount=0.02)
    }
"""

vendor_py = """
def check_vendor(name: str):
    if "New Distributor" in name:
        return {"score": 32, "badge": "red", "reasons": ["Registered 4 months ago", "Two cheque-bounce cases", "Missing GST filings", "Adverse media found"]}
    return {"score": 85, "badge": "green", "reasons": ["Registered 5 years ago", "Clean legal history", "Regular GST filings"]}
"""

llm_py = """
import re
def parse_scenario(text: str):
    match = re.search(r'(\d+)\s*days?', text)
    days = int(match.group(1)) if match else 14
    return {"type": "supplier_delay", "target": "A", "days": days}
"""

report_py = """
from reportlab.pdfgen import canvas
import io

def generate_report():
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, "BizSim Decision Report")
    c.drawString(100, 700, "Situation: Supplier delay")
    c.drawString(100, 650, "Recommended Action: Combined")
    c.save()
    buf.seek(0)
    return buf
"""

main_py = """
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
"""

write_file("backend/requirements.txt", backend_reqs)
write_file("backend/.env.example", backend_env)
write_file("backend/app/models.py", models_py)
write_file("backend/app/db.py", db_py)
write_file("backend/app/seed.py", seed_py)
write_file("backend/app/engine/cascade.py", cascade_py)
write_file("backend/app/engine/actions.py", actions_py)
write_file("backend/app/signals/vendor.py", vendor_py)
write_file("backend/app/signals/llm.py", llm_py)
write_file("backend/app/explain/report.py", report_py)
write_file("backend/app/main.py", main_py)

print("Backend files generated successfully.")
