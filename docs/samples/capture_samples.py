"""Capture real API responses into docs/samples/.

Run while the backend is up:
    cd backend && python -m uvicorn app.main:app --port 8000
    PYTHONIOENCODING=utf-8 python docs/samples/capture_samples.py

Every value written here is copied verbatim from the live API responses,
never invented. Long lists are trimmed (first 6 items + a count marker)
so the files stay readable; see docs/api_contract_engine.md for shapes.
"""

import json
import sys
import urllib.request
import uuid
from pathlib import Path

BASE = "http://localhost:8000"
OUT = Path(__file__).parent
TRIM_TO = 6


def trim(obj):
    """Recursively shorten long lists so samples stay readable."""
    if isinstance(obj, list):
        if len(obj) > 8:
            head = [trim(x) for x in obj[:TRIM_TO]]
            head.append({"trimmed": f"{len(obj) - TRIM_TO} more items omitted"})
            return head
        return [trim(x) for x in obj]
    if isinstance(obj, dict):
        return {k: trim(v) for k, v in obj.items()}
    return obj


def call(method: str, path: str, payload=None, raw=False):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as res:
        body = res.read()
        if raw:
            return body
        return json.loads(body)


def save_json(name: str, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"saved {name}  ({p.stat().st_size:,} bytes)")


def save_raw(name: str, body: bytes):
    p = OUT / name
    p.write_bytes(body)
    print(f"saved {name}  ({p.stat().st_size:,} bytes)")


def multipart(filename: str, content: bytes, field: str = "file"):
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def main() -> int:
    failures = []

    def attempt(name, method, path, payload=None, raw=False):
        try:
            return call(method, path, payload, raw)
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures.append(f"{name}: {exc}")
            return None

    # Simple GETs
    health = attempt("health", "GET", "/health")
    if health is not None:
        save_json("health.json", health)

    business = attempt("business", "GET", "/api/business")
    if business is not None:
        save_json("business.json", trim(business))

    attention = attempt("attention", "GET", "/api/attention")
    if attention is not None:
        save_json("attention.json", attention)

    forecast = attempt("forecast", "GET", "/api/forecast")
    if forecast is not None:
        save_json("forecast.json", forecast)

    anomalies = attempt("anomalies", "GET", "/api/anomalies")
    if anomalies is not None:
        save_json("anomalies.json", anomalies)

    # Cascade runs
    delay14 = attempt(
        "cascade_delay14",
        "POST",
        "/api/simulate/cascade",
        {"delay": 14, "demand_band_pct": 20,
         "scenario": {"type": "supplier_delay", "target": "A", "magnitude": 14}},
    )
    if delay14 is not None:
        save_json("cascade_delay14.json", trim(delay14))

    spike30 = attempt(
        "cascade_cost_spike30",
        "POST",
        "/api/simulate/cascade",
        {"delay": 0, "scenario": {"type": "cost_spike", "target": "", "magnitude": 30}},
    )
    if spike30 is None:
        spike30 = attempt(
            "cascade_cost_spike30",
            "POST",
            "/api/simulate/cascade",
            {"delay": 0, "scenario": {"type": "cost_spike", "target": "A", "magnitude": 30}},
        )
    if spike30 is not None:
        save_json("cascade_cost_spike30.json", trim(spike30))

    cust7 = attempt(
        "cascade_customer_delay7",
        "POST",
        "/api/simulate/cascade",
        {"delay": 0, "scenario": {"type": "customer_delay", "target": "Verma", "magnitude": 7}},
    )
    if cust7 is not None:
        save_json("cascade_customer_delay7.json", trim(cust7))

    actions = attempt("actions_delay14", "POST", "/api/actions/compare", {"delay": 14})
    if actions is not None:
        save_json("actions_delay14.json", trim(actions))

    # Pricing
    pricing = attempt(
        "pricing_whatif_fans_plus10",
        "POST",
        "/api/pricing/whatif",
        {"product_id": "fans", "price_change_pct": 10, "horizon_days": 30},
    )
    if pricing is not None:
        save_json("pricing_whatif_fans_plus10.json", trim(pricing))

    # Scenario parser
    parsed = attempt("scenario_parse", "POST", "/api/scenario/parse",
                     {"text": "Supplier A is 14 days late"})
    if parsed is not None:
        save_json("scenario_parse.json", parsed)

    # Vendor check (mock registry): red case and green case
    vend_red = attempt("vendor_check_new_distributor", "POST", "/api/vendor/check",
                       {"name": "New Distributor"})
    if vend_red is not None:
        save_json("vendor_check_new_distributor.json", vend_red)
    vend_green = attempt("vendor_check_supplier_a", "POST", "/api/vendor/check",
                         {"name": "Supplier A"})
    if vend_green is not None:
        save_json("vendor_check_supplier_a.json", vend_green)

    # Bill scan is a stub endpoint; capture with a dummy upload.
    try:
        body, headers = multipart("sample_bill.txt", b"dummy invoice content")
        req = urllib.request.Request(BASE + "/api/bill/scan", data=body,
                                     headers=headers, method="POST")
        with urllib.request.urlopen(req) as res:
            save_json("bill_scan_stub.json", json.loads(res.read()))
    except Exception as exc:  # noqa: BLE001
        failures.append(f"bill_scan_stub: {exc}")

    # Report PDF (binary)
    report = attempt("report", "GET", "/api/report", raw=True)
    if report is not None:
        save_raw("report.pdf", report)

    if failures:
        print("\nFAILURES:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("\nAll samples captured.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
