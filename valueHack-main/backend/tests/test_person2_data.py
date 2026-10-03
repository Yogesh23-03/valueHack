"""Unit tests for Person 2 data, forecast, and anomaly detection engines."""

from __future__ import annotations

import pytest

from app.data.generate import (
    PLANTED_ANOMALIES,
    generate_full_demo_dataset,
    generate_synthetic_sales,
)
from app.engine.anomaly import (
    detect_bill_anomalies,
    detect_cost_anomalies,
    detect_sales_anomalies,
    run_full_anomaly_detection,
)
from app.engine.csv_loader import (
    CSV_INVALID_DATE,
    CSV_MISSING_COLUMN,
    CSV_NEGATIVE_STOCK,
    CSV_UNKNOWN_SUPPLIER,
    parse_and_validate_csv,
)
from app.engine.errors import EngineError
from app.engine.forecast import (
    _calculate_mape,
    forecast_product_demand,
    generate_business_forecast,
)


# ==============================================================================
# Generator tests
# ==============================================================================

def test_generator_produces_90_days():
    daily_sales, daily_summaries, bills = generate_synthetic_sales(days=90, seed=42)
    assert len(daily_summaries) == 90
    assert len(daily_sales) == 90 * 3  # 3 products: fans, wiring, switches


def test_generator_has_expected_products():
    dataset = generate_full_demo_dataset(seed=42)
    product_names = {p["name"] for p in dataset["products"]}
    assert product_names == {"fans", "wiring", "switches"}


def test_generator_is_reproducible_with_seed():
    sales1, sum1, _ = generate_synthetic_sales(days=90, seed=42)
    sales2, sum2, _ = generate_synthetic_sales(days=90, seed=42)
    sales_diff, sum_diff, _ = generate_synthetic_sales(days=90, seed=999)

    assert [s["units_sold"] for s in sales1] == [s["units_sold"] for s in sales2]
    assert [s["total_cost"] for s in sum1] == [s["total_cost"] for s in sum2]
    # Different seed gives different noise
    assert [s["units_sold"] for s in sales1] != [s["units_sold"] for s in sales_diff]


def test_generator_planted_anomalies_exist():
    dataset = generate_full_demo_dataset(seed=42)
    assert len(dataset["planted_anomalies"]) == 3

    # High-cost anomaly on Day 45
    day_45 = next(d for d in dataset["daily_summaries"] if d["day_index"] == 45)
    assert day_45["total_cost"] > 45000.0  # Normal is ~22,000

    # Low-sales anomaly on Day 70
    day_70 = next(d for d in dataset["daily_summaries"] if d["day_index"] == 70)
    assert day_70["revenue"] == 0.0

    # Overpriced bill on Day 55
    anomaly_bill = next((b for b in dataset["bills"] if b.get("is_anomaly")), None)
    assert anomaly_bill is not None
    assert anomaly_bill["amount"] == 125000.0


# ==============================================================================
# Forecasting tests
# ==============================================================================

def test_forecast_returns_30_days_with_bounds():
    daily_sales, _, _ = generate_synthetic_sales(days=90, seed=42)
    fans_series = [s["units_sold"] for s in daily_sales if s["product_name"] == "fans"]

    res = forecast_product_demand(fans_series, forecast_days=30, holdout_days=14)
    assert len(res["predicted_demand"]) == 30
    assert len(res["dates"]) == 30
    assert len(res["lower_bound"]) == 30
    assert len(res["upper_bound"]) == 30

    # Upper bounds should be >= lower bounds
    for lower, upper in zip(res["lower_bound"], res["upper_bound"]):
        assert upper >= lower


def test_forecast_holdout_and_mape():
    daily_sales, _, _ = generate_synthetic_sales(days=90, seed=42)
    fans_series = [s["units_sold"] for s in daily_sales if s["product_name"] == "fans"]

    res = forecast_product_demand(fans_series, forecast_days=30, holdout_days=14)
    backtest = res["backtest"]
    assert backtest["holdout_days"] == 14
    assert len(backtest["comparison"]) == 14
    assert 0.0 <= backtest["mape"] <= 100.0


def test_forecast_zero_actual_demand_safe():
    # Verify zero-division protection
    actual = [0.0, 5.0, 0.0, 10.0]
    predicted = [0.0, 5.0, 2.0, 10.0]
    mape = _calculate_mape(actual, predicted)
    assert isinstance(mape, float)
    assert not (mape != mape)  # not NaN


def test_multi_product_business_forecast():
    fc = generate_business_forecast(forecast_days=30, holdout_days=14)
    assert fc["status"] == "success"
    assert "fans" in fc["products"]
    assert "wiring" in fc["products"]
    assert "switches" in fc["products"]
    assert fc["overall_mape"] > 0.0


# ==============================================================================
# Anomaly detection tests
# ==============================================================================

def test_anomaly_detects_planted_high_cost():
    _, summaries, _ = generate_synthetic_sales(days=90, seed=42)
    anomalies = detect_cost_anomalies(summaries)
    assert len(anomalies) >= 1
    # Day 45 (2025-12-17) must be detected
    day_45_flag = any(a["day_index"] == 45 for a in anomalies)
    assert day_45_flag, f"Day 45 high-cost anomaly was not detected in: {anomalies}"


def test_anomaly_detects_planted_low_sales():
    _, summaries, _ = generate_synthetic_sales(days=90, seed=42)
    anomalies = detect_sales_anomalies(summaries)
    assert len(anomalies) >= 1
    # Day 70 (2026-01-11) must be detected
    day_70_flag = any(a["day_index"] == 70 for a in anomalies)
    assert day_70_flag, f"Day 70 low-sales anomaly was not detected in: {anomalies}"


def test_anomaly_detects_planted_overpriced_bill():
    _, _, bills = generate_synthetic_sales(days=90, seed=42)
    anomalies = detect_bill_anomalies(bills)
    assert len(anomalies) >= 1
    overpriced_flag = any(a["value"] == 125000.0 for a in anomalies)
    assert overpriced_flag, f"Overpriced bill anomaly not detected in: {anomalies}"


def test_full_anomaly_detection_response_structure():
    res = run_full_anomaly_detection()
    assert res["status"] == "success"
    assert len(res["anomalies"]) >= 3
    for a in res["anomalies"]:
        assert "date" in a
        assert "metric" in a
        assert "value" in a
        assert "reason" in a
        assert "severity" in a


# ==============================================================================
# CSV Validator tests
# ==============================================================================

def test_csv_valid_products_loads():
    content = """name,price,cost,demand_per_day,opening_stock,supplier_name
fans,1900,1400,4,36,Supplier A
wiring,1200,900,6,54,Supplier A
"""
    table, rows = parse_and_validate_csv(content)
    assert table == "products"
    assert len(rows) == 2
    assert rows[0]["name"] == "fans"
    assert float(rows[0]["price"]) == 1900.0


def test_csv_missing_column_rejected():
    content = """name,cost,demand_per_day,opening_stock
fans,1400,4,36
"""
    with pytest.raises(EngineError) as exc_info:
        parse_and_validate_csv(content, table_type="products")
    assert exc_info.value.code == CSV_MISSING_COLUMN
    assert "price" in exc_info.value.message


def test_csv_negative_stock_rejected():
    content = """name,price,cost,demand_per_day,opening_stock
fans,1900,1400,4,-10
"""
    with pytest.raises(EngineError) as exc_info:
        parse_and_validate_csv(content)
    assert exc_info.value.code == CSV_NEGATIVE_STOCK
    assert "fans" in exc_info.value.message
    assert "-10" in exc_info.value.message


def test_csv_invalid_date_rejected():
    content = """bill_number,supplier_name,amount,date,due_date
INV-001,Supplier A,275000,2026/13/45,2026-02-15
"""
    with pytest.raises(EngineError) as exc_info:
        parse_and_validate_csv(content, table_type="bills")
    assert exc_info.value.code == CSV_INVALID_DATE
    assert "date" in exc_info.value.message.lower()
