"""HTTP integration tests for Person 2 endpoints."""

from __future__ import annotations

import io
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["ok"] is True


def test_forecast_endpoint(client: TestClient):
    res = client.get("/api/forecast")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "products" in data
    assert "fans" in data["products"]
    assert len(data["products"]["fans"]["predicted_demand"]) == 30
    assert data["overall_mape"] > 0


def test_anomalies_endpoint(client: TestClient):
    res = client.get("/api/anomalies")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_anomalies"] >= 3
    # Check that high cost, low sales, and overpriced bill anomalies are returned
    metrics = {a["metric"] for a in data["anomalies"]}
    assert "cost" in metrics
    assert "sales" in metrics
    assert "bill" in metrics


def test_attention_endpoint_includes_anomalies(client: TestClient):
    res = client.get("/api/attention")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    assert len(items) > 0

    # Ensure frontend compatibility fields exist
    for item in items:
        assert "id" in item
        assert "text" in item
        assert "icon" in item

    # Ensure anomaly items are included in attention
    has_anomaly = any(item.get("type") == "anomaly" for item in items)
    assert has_anomaly, "No anomaly items found in /api/attention response"


def test_api_business_load_valid_products(client: TestClient):
    csv_content = b"""name,price,cost,demand_per_day,opening_stock,supplier_name
fans,1900,1400,4,36,Supplier A
wiring,1200,900,6,54,Supplier A
"""
    files = {"file": ("products.csv", io.BytesIO(csv_content), "text/csv")}
    res = client.post("/api/business/load", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["table"] == "products"
    assert data["rows_loaded"] == 2


def test_api_business_load_rejects_missing_column(client: TestClient):
    csv_content = b"""name,cost,demand_per_day,opening_stock
fans,1400,4,36
"""
    files = {"file": ("products.csv", io.BytesIO(csv_content), "text/csv")}
    res = client.post("/api/business/load?table_type=products", files=files)
    assert res.status_code == 422
    data = res.json()
    assert data["code"] == "CSV_MISSING_COLUMN"
    assert "price" in data["message"]


def test_api_business_load_rejects_negative_stock(client: TestClient):
    csv_content = b"""name,price,cost,demand_per_day,opening_stock
fans,1900,1400,4,-10
"""
    files = {"file": ("products.csv", io.BytesIO(csv_content), "text/csv")}
    res = client.post("/api/business/load", files=files)
    assert res.status_code == 422
    data = res.json()
    assert data["code"] == "CSV_NEGATIVE_STOCK"
    assert "Product 'fans' has negative stock: -10" in data["message"]


def test_api_business_load_rejects_invalid_date(client: TestClient):
    csv_content = b"""bill_number,supplier_name,amount,date,due_date
INV-001,Supplier A,275000,2026-99-99,2026-02-15
"""
    files = {"file": ("bills.csv", io.BytesIO(csv_content), "text/csv")}
    res = client.post("/api/business/load", files=files)
    assert res.status_code == 422
    data = res.json()
    assert data["code"] == "CSV_INVALID_DATE"
