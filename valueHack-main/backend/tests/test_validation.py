"""Validation tests: the engine uses one error format ``{code, message}``."""

from __future__ import annotations

import pytest

from app.engine.errors import EngineError
from app.engine.models import Plan, Shock


def test_invalid_shock_type(business):
    from app.engine.sim import simulate_plan

    with pytest.raises(EngineError) as exc:
        simulate_plan(business, Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=1)).model_copy(
            update={"shock": Shock.model_construct(type="earthquake", target="x", magnitude=1)}
        ))
    assert exc.value.code == "INVALID_SHOCK"


def test_unknown_supplier(business):
    from app.engine.sim import simulate_plan

    with pytest.raises(EngineError) as exc:
        simulate_plan(business, Plan(shock=Shock(type="supplier_delay", target="nope", magnitude=3)))
    assert exc.value.code == "UNKNOWN_SUPPLIER"
    assert exc.value.status == 404


def test_magnitude_out_of_range(business):
    from app.engine.sim import simulate_plan

    with pytest.raises(EngineError) as exc:
        simulate_plan(business, Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=9999)))
    assert exc.value.code == "MAGNITUDE_OUT_OF_RANGE"


def test_elasticity_out_of_range(business):
    from app.engine.pricing import price_whatif

    with pytest.raises(EngineError) as exc:
        price_whatif(business, "fans", 10, elasticity=-5)
    assert exc.value.code == "ELASTICITY_OUT_OF_RANGE"


def test_error_format_over_http(client):
    r = client.post(
        "/api/simulate/cascade",
        json={"scenario": {"type": "supplier_delay", "target": "nope", "magnitude": 3}},
    )
    assert r.status_code == 404
    assert set(r.json().keys()) == {"code", "message"}
    assert r.json()["code"] == "UNKNOWN_SUPPLIER"

    r = client.post("/api/pricing/whatif", json={"product_id": "fans", "price_change_pct": 10, "elasticity": -9})
    assert r.status_code == 422
    assert r.json()["code"] == "ELASTICITY_OUT_OF_RANGE"

    r = client.post(
        "/api/simulate/cascade",
        json={"scenario": {"type": "earthquake", "target": "x", "magnitude": 1}},
    )
    assert r.status_code == 422
    assert r.json()["code"] == "INVALID_SHOCK"
