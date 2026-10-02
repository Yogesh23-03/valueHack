"""Demand-band ranges.

Reruns the simulation at a low, base and high demand multiplier so the UI can
show ranges instead of false precision. A metric's ``min`` and ``max`` are taken
from the runs, and the case that produced each is recorded.
"""

from __future__ import annotations

from .models import Business, Plan, RangeCase, RangeMetric, Ranges

RANGED_METRICS = [
    "stockout_day",
    "lost_sales_inr",
    "first_negative_day",
    "lowest_cash_inr",
    "lowest_cash_day",
    "end_cash_inr",
]

CASES = [("low", 0.8), ("base", 1.0), ("high", 1.2)]


def _numeric_key(metric: str, value, horizon: int) -> float:
    """A sortable key where ``None`` means "later than the horizon" for days."""
    if value is None:
        return float(horizon + 1) if metric.endswith("_day") or metric == "stockout_day" else 0.0
    return float(value)


def compute_ranges(
    business: Business,
    plan: Plan,
    *,
    demand_band_pct: float = 20.0,
    horizon: int | None = None,
) -> Ranges:
    """Run low/base/high demand and return the range envelope."""
    horizon = horizon or business.horizon_days
    band = demand_band_pct / 100.0
    cases = [("low", 1.0 - band), ("base", 1.0), ("high", 1.0 + band)]

    # Imported here to avoid a circular import at module load.
    from .sim import simulate_plan

    runs: list[RangeCase] = []
    for case_name, multiplier in cases:
        run_plan = plan.model_copy(update={"demand_multiplier": multiplier})
        result = simulate_plan(business, run_plan, with_ranges=False, light=True)
        metrics = {m: result.summary.get(m) for m in RANGED_METRICS}
        runs.append(RangeCase(case=case_name, demand_multiplier=round(multiplier, 4), metrics=metrics))

    metrics: dict[str, RangeMetric] = {}
    for metric in RANGED_METRICS:
        best_idx = min(range(len(runs)), key=lambda i: _numeric_key(metric, runs[i].metrics[metric], horizon))
        worst_idx = max(range(len(runs)), key=lambda i: _numeric_key(metric, runs[i].metrics[metric], horizon))
        base_run = next(r for r in runs if r.case == "base")
        metrics[metric] = RangeMetric(
            min=runs[best_idx].metrics[metric],
            base=base_run.metrics[metric],
            max=runs[worst_idx].metrics[metric],
            min_case=runs[best_idx].case,
            max_case=runs[worst_idx].case,
        )

    return Ranges(runs=runs, metrics=metrics, range_note=_range_note(demand_band_pct, metrics))


def _range_note(band_pct: float, metrics: dict[str, RangeMetric]) -> str:
    neg = metrics.get("first_negative_day")
    if neg is None:
        return ""
    if neg.base is None and neg.max is None:
        return (
            f"Across demand {_fmt_pct(band_pct)} lower to {_fmt_pct(band_pct)} higher, "
            "cash stays positive throughout."
        )
    days = [d for d in (neg.min, neg.base, neg.max) if d is not None]
    if not days:
        return "Across the demand band, no cash gap appears."
    if len(set(int(d) for d in days)) == 1:
        return (
            f"Across demand {_fmt_pct(band_pct)} lower to {_fmt_pct(band_pct)} higher, "
            f"cash first goes below zero on day {int(days[0])} in every case."
        )
    return (
        f"Across demand {_fmt_pct(band_pct)} lower to {_fmt_pct(band_pct)} higher, "
        f"cash first goes below zero between day {int(min(days))} and day {int(max(days))}."
    )


def _fmt_pct(value: float) -> str:
    v = int(value) if float(value).is_integer() else value
    return f"{v} percent"
