"""Demand forecasting engine for BizSim.

Implements:
1. 30-day product demand forecast using Holt-Winters Exponential Smoothing
   (or robust Seasonal-Trend Moving Average fallback).
2. Prediction bounds (upper and lower ranges).
3. 14-day holdout backtest calculating Mean Absolute Percentage Error (MAPE)
   with zero-division protection.

Pure numerical forecasting based on historical sales data — no LLM figures.
"""

from __future__ import annotations

import datetime
import math
from typing import Any, Optional


def _calculate_mape(actual: list[float], predicted: list[float]) -> float:
    """Calculate Mean Absolute Percentage Error (MAPE) safely.

    Handles actual == 0 by avoiding division-by-zero errors.
    """
    if not actual or len(actual) != len(predicted):
        return 0.0

    errors: list[float] = []
    for act, pred in zip(actual, predicted):
        if act > 0:
            errors.append(abs(act - pred) / act)
        elif act == 0 and pred > 0:
            # If actual demand was 0 but we predicted > 0, penalize normalized by unit scale
            errors.append(min(1.0, abs(pred)))
        else:
            errors.append(0.0)

    if not errors:
        return 0.0
    return round(float(sum(errors) / len(errors)) * 100.0, 2)


def _seasonal_fallback_forecast(
    series: list[float],
    forecast_steps: int = 30,
    period: int = 7,
) -> tuple[list[float], list[float], list[float]]:
    """Seasonal average fallback when statsmodels is unavailable or non-convergent.

    Computes 7-day weekly seasonality indices plus underlying moving average level.
    """
    n = len(series)
    if n < period:
        mean_val = sum(series) / max(1, n)
        pred = [max(0.0, round(mean_val, 1)) for _ in range(forecast_steps)]
        return pred, [max(0.0, p * 0.8) for p in pred], [p * 1.2 for p in pred]

    # Calculate overall average and day-of-week seasonal factors
    dow_sums = [0.0] * period
    dow_counts = [0] * period
    for idx, val in enumerate(series):
        dow = idx % period
        dow_sums[dow] += val
        dow_counts[dow] += 1

    dow_means = [dow_sums[i] / max(1, dow_counts[i]) for i in range(period)]
    overall_mean = sum(dow_means) / period if period > 0 else 1.0

    seasonal_factors = [(m / overall_mean) if overall_mean > 0 else 1.0 for m in dow_means]

    # Baseline level from recent 14 days
    recent = series[-min(n, 14):]
    recent_level = sum(recent) / len(recent) if recent else overall_mean

    # Sample standard deviation for confidence interval
    residuals = []
    for idx, val in enumerate(series):
        expected = overall_mean * seasonal_factors[idx % period]
        residuals.append(val - expected)
    variance = sum(r * r for r in residuals) / max(1, len(residuals) - 1)
    std_dev = math.sqrt(variance)

    predictions: list[float] = []
    lower_bounds: list[float] = []
    upper_bounds: list[float] = []

    for step in range(forecast_steps):
        target_idx = (n + step) % period
        pred = max(0.0, recent_level * seasonal_factors[target_idx])
        pred = round(pred, 2)
        lower = max(0.0, round(pred - 1.28 * std_dev, 2))  # 80% lower bound
        upper = round(pred + 1.28 * std_dev, 2)            # 80% upper bound

        predictions.append(pred)
        lower_bounds.append(lower)
        upper_bounds.append(upper)

    return predictions, lower_bounds, upper_bounds


def forecast_product_demand(
    sales_series: list[float],
    forecast_days: int = 30,
    holdout_days: int = 14,
    start_forecast_date: Optional[str] = None,
) -> dict[str, Any]:
    """Perform a 14-day holdout backtest and generate a 30-day forecast for a single product.

    Parameters
    ----------
    sales_series:
        List of daily demand values (e.g. 90 days).
    forecast_days:
        Horizon to predict forward (default: 30 days).
    holdout_days:
        Holdout window for backtest (default: 14 days).
    start_forecast_date:
        ISO date (YYYY-MM-DD) for day 1 of the forecast period.
    """
    total_days = len(sales_series)
    if total_days < holdout_days + 7:
        raise ValueError(f"Need at least {holdout_days + 7} days of data; got {total_days}")

    # 1. 14-Day Holdout Backtest
    train_data = sales_series[:-holdout_days]
    actual_holdout = sales_series[-holdout_days:]

    # Fit model on training slice
    predicted_holdout: list[float] = []
    used_statsmodels = False

    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            hw_train = ExponentialSmoothing(
                train_data,
                trend="add",
                seasonal="add",
                seasonal_periods=7,
                initialization_method="estimated",
            ).fit()
            raw_pred = hw_train.forecast(holdout_days)
            predicted_holdout = [max(0.0, round(float(p), 2)) for p in raw_pred]
            used_statsmodels = True
    except Exception:
        # Fallback to robust seasonal moving average
        predicted_holdout, _, _ = _seasonal_fallback_forecast(
            train_data, forecast_steps=holdout_days, period=7
        )

    mape = _calculate_mape(actual_holdout, predicted_holdout)

    # 2. Next 30-Day Forecast based on full history
    predicted_future: list[float] = []
    lower_bounds: list[float] = []
    upper_bounds: list[float] = []

    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            hw_full = ExponentialSmoothing(
                sales_series,
                trend="add",
                seasonal="add",
                seasonal_periods=7,
                initialization_method="estimated",
            ).fit()
            raw_future = hw_full.forecast(forecast_days)
            predicted_future = [max(0.0, round(float(p), 2)) for p in raw_future]

            # Approximate confidence intervals using in-sample residual standard error
            residuals = hw_full.resid
            var = sum(r * r for r in residuals) / max(1, len(residuals) - 1)
            sigma = math.sqrt(var)
            lower_bounds = [max(0.0, round(p - 1.28 * sigma, 2)) for p in predicted_future]
            upper_bounds = [round(p + 1.28 * sigma, 2) for p in predicted_future]
            used_statsmodels = True
    except Exception:
        predicted_future, lower_bounds, upper_bounds = _seasonal_fallback_forecast(
            sales_series, forecast_steps=forecast_days, period=7
        )

    # Generate dates for forecast
    if start_forecast_date:
        base_d = datetime.date.fromisoformat(start_forecast_date)
    else:
        base_d = datetime.date.today()

    forecast_dates = [(base_d + datetime.timedelta(days=i)).isoformat() for i in range(forecast_days)]

    holdout_comparison = [
        {
            "day_index": total_days - holdout_days + idx + 1,
            "actual": actual_holdout[idx],
            "predicted": predicted_holdout[idx],
            "error_pct": round(
                abs(actual_holdout[idx] - predicted_holdout[idx]) / actual_holdout[idx] * 100.0, 2
            )
            if actual_holdout[idx] > 0
            else 0.0,
        }
        for idx in range(holdout_days)
    ]

    return {
        "model": "Holt-Winters Exponential Smoothing" if used_statsmodels else "Seasonal Moving Average Fallback",
        "history_days": total_days,
        "forecast_days": forecast_days,
        "dates": forecast_dates,
        "predicted_demand": predicted_future,
        "lower_bound": lower_bounds,
        "upper_bound": upper_bounds,
        "backtest": {
            "holdout_days": holdout_days,
            "mape": mape,
            "comparison": holdout_comparison,
        },
    }


def generate_business_forecast(
    daily_sales: Optional[list[dict[str, Any]]] = None,
    forecast_days: int = 30,
    holdout_days: int = 14,
) -> dict[str, Any]:
    """Generate multi-product demand forecast and holdout backtest for BizSim.

    Parameters
    ----------
    daily_sales:
        List of daily product sales dicts. If None, uses synthetic 90-day generator.
    forecast_days:
        Days to forecast ahead (30).
    holdout_days:
        Holdout window for backtest (14).

    Returns
    -------
    Dictionary with per-product forecasts, MAPE backtest scores, and overall metrics.
    """
    if daily_sales is None:
        from ..data.generate import generate_synthetic_sales

        daily_sales, _, _ = generate_synthetic_sales(days=90, seed=42)

    # Group series by product
    by_product: dict[str, list[dict[str, Any]]] = {}
    for row in daily_sales:
        by_product.setdefault(row["product_name"], []).append(row)

    # Sort each product by day_index
    for p in by_product:
        by_product[p].sort(key=lambda x: x["day_index"])

    results_by_product: dict[str, Any] = {}
    mapes: list[float] = []

    last_date = daily_sales[-1]["date"] if daily_sales else None
    next_day = None
    if last_date:
        next_day = (datetime.date.fromisoformat(last_date) + datetime.timedelta(days=1)).isoformat()

    for product_name, records in by_product.items():
        series = [float(r["units_sold"]) for r in records]
        fc = forecast_product_demand(
            sales_series=series,
            forecast_days=forecast_days,
            holdout_days=holdout_days,
            start_forecast_date=next_day,
        )
        results_by_product[product_name] = fc
        mapes.append(fc["backtest"]["mape"])

    overall_mape = round(sum(mapes) / max(1, len(mapes)), 2)

    return {
        "status": "success",
        "method": "Holt-Winters Exponential Smoothing",
        "overall_mape": overall_mape,
        "holdout_days": holdout_days,
        "forecast_days": forecast_days,
        "products": results_by_product,
    }
