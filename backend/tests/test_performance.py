"""Timing tests: the demand-band runs behind the sliders must feel instant.

``compare_actions`` runs every action at low/base/high demand. The whole
comparison must finish well under 300 ms so the UI can respond immediately.
"""

from __future__ import annotations

import time


def test_compare_actions_under_300ms(business):
    from app.engine.actions import compare_actions

    # Warm up so first-call import/parse cost does not count.
    compare_actions(14, business)

    start = time.perf_counter()
    compare_actions(14, business)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 300, f"compare_actions took {elapsed_ms:.1f} ms"


def test_ranges_under_300ms(business):
    from app.engine.models import Plan, Shock
    from app.engine.ranges import compute_ranges

    plan = Plan(shock=Shock(type="supplier_delay", target="sup_a", magnitude=14))
    start = time.perf_counter()
    compute_ranges(business, plan)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 300, f"compute_ranges took {elapsed_ms:.1f} ms"
