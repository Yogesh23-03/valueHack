"""Characterization (golden) tests.

These freeze the response the frontend already reads. The legacy fields keep
their names, types and meaning after the engine refactor; new fields are added
alongside. Fixtures live in ``tests/golden/``.
"""

from __future__ import annotations

import json
import pathlib

GOLDEN_DIR = pathlib.Path(__file__).resolve().parent / "golden"

LEGACY_CASCADE_FIELDS = [
    "stockout",
    "lost_rev",
    "first_negative_day",
    "min_cash",
    "min_day",
    "failed",
    "delivered",
    "end_cash",
    "cash_timeline",
    "stock_timeline",
]

NEW_CASCADE_FIELDS = [
    "scenario",
    "summary",
    "cascade_chain",
    "events",
    "timeline",
    "explanations",
    "assumptions",
    "ranges",
    "meta",
]


def _load(name: str) -> dict:
    return json.loads((GOLDEN_DIR / name).read_text(encoding="utf-8"))


def test_golden_business_fields(client):
    golden = _load("business.json")
    current = client.get("/api/business").json()
    assert current["name"] == golden["name"]
    assert current["cash"] == golden["cash"]
    assert set(current["analytics"].keys()) == set(golden["analytics"].keys())


def test_golden_cascade_legacy_fields_unchanged(client):
    for name, payload in [("cascade_baseline.json", {"delay": 0}), ("cascade_delay14.json", {"delay": 14})]:
        golden = _load(name)
        current = client.post("/api/simulate/cascade", json=payload).json()
        for field in LEGACY_CASCADE_FIELDS:
            assert field in current, f"{field} missing after refactor"
            assert current[field] == golden[field], f"{field} changed for {name}"
        for field in NEW_CASCADE_FIELDS:
            assert field in current, f"new field {field} missing"


def test_golden_actions_legacy_fields_unchanged(client):
    golden = _load("actions_delay14.json")
    current = client.post("/api/actions/compare", json={"delay": 14}).json()
    # Every legacy action id still returns its old fields with the same types.
    for key in ["do_nothing", "ask_extension", "early_discount", "switch_vendor", "combined"]:
        assert key in current
        for field in ["min_cash", "cash_timeline", "failed"]:
            assert field in current[key]
            assert type(current[key][field]) is type(golden[key][field])
    # The combined action still drives the chart.
    assert current["combined"]["cash_timeline"] == golden["combined"]["cash_timeline"]
