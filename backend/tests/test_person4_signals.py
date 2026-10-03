"""Unit and integration tests for Person 4 (Signals, Vendor Checks, Bill Scan, PDF Reports)."""

from fastapi.testclient import TestClient

from app.explain.report import generate_report
from app.main import app
from app.signals.bills import audit_extracted_bill, parse_bill_file
from app.signals.gstin import gstin_checksum, gstin_valid, pan_valid
from app.signals.vendor import check_vendor


def test_gstin_checksum_and_valid():
    """Verify Appendix B test vector and checksum logic."""
    # Official Appendix B sample
    assert gstin_valid("27AAPFU0939F1ZV") is True
    assert gstin_checksum("27AAPFU0939F1Z") == "V"

    # Valid Karnataka GSTIN with computed checksum
    assert gstin_valid("29AABCS1429B1ZQ") is True

    # Bad checksum
    assert gstin_valid("27AAPFU0939F1ZX") is False

    # Bad length or character
    assert gstin_valid("INVALIDGSTIN") is False
    assert gstin_valid("27AAPFU0939F1") is False


def test_pan_valid():
    assert pan_valid("AAPFU0939F") is True
    assert pan_valid("AABCS1429B") is True
    assert pan_valid("INVALIDPAN1") is False
    assert pan_valid("12345ABCDE") is False


def test_vendor_trust_scores_by_band():
    """Test green, amber, and red vendor trust scoring."""
    # Clean vendor -> Green
    supp_a = check_vendor("Supplier A")
    assert supp_a["badge"] == "green"
    assert supp_a["score"] >= 75
    assert len(supp_a["evidence"]) > 0

    # Shell / High-risk vendor -> Red
    new_dist = check_vendor("New Distributor")
    assert new_dist["badge"] == "red"
    assert new_dist["score"] < 50
    assert any("cheque" in r.lower() or "missing" in r.lower() or "newly" in r.lower() for r in new_dist["reasons"])

    # Moderate risk vendor -> Amber
    balaji = check_vendor("Shree Balaji Components")
    assert balaji["badge"] == "amber"
    assert 50 <= balaji["score"] < 75


def test_vendor_risk_wired_to_actions():
    """Test that actions.py pulls real vendor risk and elevates risk for red vendors."""
    from app.engine.actions import compare_actions

    actions = compare_actions(delay=14)

    # Verify switch_supplier carries vendor risk
    assert "switch_supplier" in actions
    switch_action = actions["switch_supplier"]
    assert switch_action["risk"]["level"] in ("Medium", "High")
    # Verify vendor risk factor is listed in risk reasons
    risk_reasons = [f["reason"] for f in switch_action["risk"]["factors"]]
    assert any("vendor" in r.lower() or "red" in r.lower() for r in risk_reasons)


def test_bill_overcharge_detection():
    """Verify >10% overcharge detection on line items."""
    sample_data = {
        "supplier": "Apex Electricals Pvt Ltd",
        "supplier_gstin": "27AAPFU0939F1ZV",
        "items": [
            {"name": "Ceiling Fans", "hsn_code": "8414", "qty": 10, "unit_price": 1680.0, "tax_rate": 18.0},
        ],
    }
    result = audit_extracted_bill(sample_data)
    assert result["flag_count"] >= 1
    assert result["flags"][0]["type"] == "OVERCHARGE"
    assert result["flags"][0]["excess_amount_inr"] == (1680.0 - 1400.0) * 10


def test_bill_tax_mismatch_detection():
    """Verify HSN tax rate mismatch detection."""
    sample_data = {
        "supplier": "Classic Switchgears & Fittings",
        "supplier_gstin": "29AABCS1429B1ZQ",
        "items": [
            {"name": "Modular Switches", "hsn_code": "8536", "qty": 50, "unit_price": 120.0, "tax_rate": 28.0},
        ],
    }
    result = audit_extracted_bill(sample_data)
    tax_flags = [f for f in result["flags"] if f["type"] == "TAX_RATE_MISMATCH"]
    assert len(tax_flags) == 1
    assert tax_flags[0]["expected_tax"] == 18.0
    assert tax_flags[0]["actual_tax"] == 28.0


def test_pdf_report_generates_valid_stream():
    """Verify that ReportLab generates a valid PDF document."""
    buf = generate_report()
    pdf_bytes = buf.getvalue()
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


def test_api_endpoints_signals_and_reports():
    """Test HTTP API endpoints for signals, bill scan, and report."""
    with TestClient(app) as client:
        # Vendor check endpoint
        v_res = client.post("/api/vendor/check", json={"name": "New Distributor"})
        assert v_res.status_code == 200
        v_data = v_res.json()
        assert v_data["badge"] == "red"
        assert v_data["score"] < 50

        # Bill scan endpoint
        file_payload = {"file": ("invoice.pdf", b"High-Speed Ceiling Fans 1650 each", "application/pdf")}
        b_res = client.post("/api/bill/scan", files=file_payload)
        assert b_res.status_code == 200
        b_data = b_res.json()
        assert "items" in b_data
        assert "vendor_risk" in b_data

        # Report PDF endpoint
        r_res = client.get("/api/report")
        assert r_res.status_code == 200
        assert r_res.headers["content-type"] == "application/pdf"
        assert r_res.content.startswith(b"%PDF-")
