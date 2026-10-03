"""Verify all endpoints directly against the FastAPI application."""

from __future__ import annotations

import io
import sys
from fastapi.testclient import TestClient
from app.main import app

# Ensure utf-8 output encoding on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_checks():
    client = TestClient(app)

    print("--- 1. Checking GET /health ---")
    res = client.get("/health")
    print(f"Status: {res.status_code}, Response: {res.json()}")
    assert res.status_code == 200

    print("\n--- 2. Checking GET /docs ---")
    res = client.get("/docs")
    print(f"Status: {res.status_code}, HTML length: {len(res.text)}")
    assert res.status_code == 200

    print("\n--- 3. Checking GET /api/attention ---")
    res = client.get("/api/attention")
    print(f"Status: {res.status_code}, Items count: {len(res.json())}")
    for item in res.json()[:3]:
        print(f" - [{item.get('type')}/{item.get('severity')}] {item.get('text')}")
    assert res.status_code == 200

    print("\n--- 4. Checking GET /api/forecast ---")
    res = client.get("/api/forecast")
    data = res.json()
    print(f"Status: {res.status_code}, Method: {data.get('method')}, Overall MAPE: {data.get('overall_mape')}%")
    for prod, info in data.get("products", {}).items():
        print(f" - {prod}: Backtest MAPE = {info['backtest']['mape']}%, 30-day predicted avg = {round(sum(info['predicted_demand'])/30, 2)}")
    assert res.status_code == 200

    print("\n--- 5. Checking GET /api/anomalies ---")
    res = client.get("/api/anomalies")
    data = res.json()
    print(f"Status: {res.status_code}, Total anomalies detected: {data.get('total_anomalies')}")
    for a in data.get("anomalies", []):
        print(f" - [{a['metric'].upper()}] {a['date']}: {a['reason']}")
    assert res.status_code == 200

    print("\n--- 6. Checking POST /api/business/load with valid CSV ---")
    csv_valid = b"name,price,cost,demand_per_day,opening_stock,supplier_name\nfans,1900,1400,4,36,Supplier A\n"
    files = {"file": ("products.csv", io.BytesIO(csv_valid), "text/csv")}
    res = client.post("/api/business/load", files=files)
    print(f"Status: {res.status_code}, Response: {res.json()}")
    assert res.status_code == 200

    print("\n--- 7. Checking POST /api/business/load with negative stock CSV ---")
    csv_bad = b"name,price,cost,demand_per_day,opening_stock\nfans,1900,1400,4,-10\n"
    files = {"file": ("products.csv", io.BytesIO(csv_bad), "text/csv")}
    res = client.post("/api/business/load", files=files)
    print(f"Status: {res.status_code}, Response: {res.json()}")
    assert res.status_code == 422
    assert res.json()["code"] == "CSV_NEGATIVE_STOCK"

    print("\nALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_checks()
