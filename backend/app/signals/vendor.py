"""Vendor trust scoring engine based on regulatory signals, filing history, and legal records.

Computes a deterministic 0-100 score with Green/Amber/Red badges and itemized evidence.
Uses mock_vendors.json for seeded data with fallback heuristics for unknown entities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from .gstin import extract_pan_from_gstin, gstin_valid, pan_valid

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "mock_vendors.json"


def _load_mock_vendors() -> List[Dict[str, Any]]:
    if DATA_PATH.exists():
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def find_vendor_record(query: str) -> Optional[Dict[str, Any]]:
    """Look up a vendor by name, alias, GSTIN, PAN, or id."""
    query_clean = query.strip().lower()
    vendors = _load_mock_vendors()
    for v in vendors:
        if v.get("id", "").lower() == query_clean:
            return v
        if v.get("name", "").lower() == query_clean:
            return v
        if query_clean in [alias.lower() for alias in v.get("aliases", [])]:
            return v
        if v.get("gstin", "").lower() == query_clean:
            return v
        if v.get("pan", "").lower() == query_clean:
            return v
        if query_clean in v.get("name", "").lower() or v.get("name", "").lower() in query_clean:
            return v
    return None


def calculate_vendor_trust_score(
    vendor: Dict[str, Any],
    provided_gstin: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate rule-based vendor trust score (0-100), risk band, and evidence list."""
    score = 100
    reasons: List[str] = []
    evidence: List[Dict[str, Any]] = []

    gstin = provided_gstin or vendor.get("gstin", "")
    pan = vendor.get("pan") or (extract_pan_from_gstin(gstin) if gstin else None)

    # 1. GSTIN & PAN Checks
    if gstin:
        if gstin_valid(gstin):
            evidence.append({"type": "gstin", "status": "pass", "detail": f"Valid GSTIN checksum ({gstin})"})
        else:
            score -= 35
            reasons.append("Invalid GSTIN structure or failed checksum algorithm")
            evidence.append({"type": "gstin", "status": "fail", "detail": f"GSTIN checksum verification failed ({gstin})"})
    elif pan:
        if pan_valid(pan):
            score -= 10
            reasons.append("PAN verified but no registered GSTIN provided")
            evidence.append({"type": "pan", "status": "warn", "detail": f"Valid PAN ({pan}), missing GSTIN registration"})
        else:
            score -= 30
            reasons.append("Invalid PAN format")
            evidence.append({"type": "pan", "status": "fail", "detail": f"PAN format mismatch ({pan})"})
    else:
        score -= 20
        reasons.append("No GSTIN or PAN provided for identity verification")
        evidence.append({"type": "identity", "status": "warn", "detail": "Unregistered entity"})

    # 2. Company Age & Track Record
    age = vendor.get("age_years", 0.0)
    if age < 0.5:
        score -= 25
        reasons.append(f"Newly registered entity ({int(age * 12)} months old) with minimal trading history")
        evidence.append({"type": "age", "status": "fail", "detail": f"Entity age is only {age:.1f} years"})
    elif age < 1.0:
        score -= 15
        reasons.append(f"Recently incorporated business ({int(age * 12)} months old)")
        evidence.append({"type": "age", "status": "warn", "detail": f"Entity age is {age:.1f} years"})
    elif age < 3.0:
        score -= 5
        reasons.append(f"Young enterprise ({age:.1f} years old)")
        evidence.append({"type": "age", "status": "info", "detail": f"Entity age is {age:.1f} years"})
    else:
        evidence.append({"type": "age", "status": "pass", "detail": f"Established track record ({age:.1f} years active)"})

    # 3. GST Filing Compliance
    filings = vendor.get("filing_history", {})
    missing_cnt = filings.get("missing_filings_count", 0)
    delayed_cnt = filings.get("delayed_filings_count", 0)
    gstr3b_pct = filings.get("gstr3b_compliance_pct", 100)

    if missing_cnt >= 3:
        score -= 30
        reasons.append(f"{missing_cnt} missing GST tax returns in the last 12 months")
        evidence.append({"type": "filings", "status": "fail", "detail": f"{missing_cnt} missing GSTR filings (compliance {gstr3b_pct}%)"})
    elif missing_cnt > 0:
        score -= 15
        reasons.append(f"{missing_cnt} missing GST filing return(s)")
        evidence.append({"type": "filings", "status": "warn", "detail": f"{missing_cnt} missing returns"})

    if delayed_cnt >= 3:
        score -= 10
        reasons.append(f"Frequent delayed filings ({delayed_cnt} late returns)")
        evidence.append({"type": "filings", "status": "warn", "detail": f"{delayed_cnt} delayed filings"})
    elif missing_cnt == 0 and delayed_cnt == 0:
        evidence.append({"type": "filings", "status": "pass", "detail": "100% on-time GST filing compliance (GSTR-1 & 3B)"})

    # 4. Court Cases & Legal Disputes
    court_cases = vendor.get("court_cases", [])
    if court_cases:
        for case in court_cases:
            nature = case.get("nature", "").lower()
            if "cheque bounce" in nature or "ni 138" in nature or "recovery" in nature:
                score -= 25
                reasons.append(f"Active commercial court case: {case.get('nature')} ({case.get('case_no')})")
                evidence.append({"type": "legal", "status": "fail", "detail": f"{case.get('court')}: {case.get('nature')}"})
            else:
                score -= 10
                reasons.append(f"Pending legal dispute: {case.get('nature')}")
                evidence.append({"type": "legal", "status": "warn", "detail": f"{case.get('court')}: {case.get('nature')}"})
    else:
        evidence.append({"type": "legal", "status": "pass", "detail": "No pending court cases or cheque-bounce records"})

    # 5. Insolvency / NCLT
    if vendor.get("insolvency_proceedings", False):
        score -= 40
        reasons.append("Active NCLT corporate insolvency resolution proceeding (IBC Section 9)")
        evidence.append({"type": "insolvency", "status": "fail", "detail": "NCLT CIRP proceeding initiated"})

    # 6. Frequent Governance / Address Shifts
    dir_changes = vendor.get("director_changes_last_2yr", 0)
    addr_changes = vendor.get("address_changes_last_2yr", 0)
    if dir_changes >= 2:
        score -= 15
        reasons.append(f"Frequent management turnover ({dir_changes} director changes in 24 months)")
        evidence.append({"type": "governance", "status": "warn", "detail": f"{dir_changes} director resignations/appointments in 2 years"})
    if addr_changes >= 2:
        score -= 10
        reasons.append(f"Unstable premises ({addr_changes} registered address changes in 24 months)")
        evidence.append({"type": "premises", "status": "warn", "detail": f"{addr_changes} address changes in 2 years"})

    # 7. Adverse Media
    adverse = vendor.get("adverse_media", [])
    if adverse:
        for news in adverse:
            score -= 15
            reasons.append(f"Adverse media signal: {news.get('headline')}")
            evidence.append({"type": "adverse_media", "status": "fail", "detail": f"{news.get('source')}: {news.get('headline')}"})

    # Clamping & Badge determination
    final_score = max(5, min(100, score))
    if final_score >= 75:
        badge = "green"
        risk_level = "Low"
        if not reasons:
            reasons.append("Clean compliance history, verified GSTIN, and established operations.")
    elif final_score >= 50:
        badge = "amber"
        risk_level = "Medium"
        if not reasons:
            reasons.append("Moderate risk signals detected in filings or corporate stability.")
    else:
        badge = "red"
        risk_level = "High"
        if not reasons:
            reasons.append("High risk entity with severe red flags in legal, filing, or identity checks.")

    return {
        "name": vendor.get("name", "Unknown Vendor"),
        "id": vendor.get("id", "vendor"),
        "gstin": gstin,
        "pan": pan,
        "score": final_score,
        "badge": badge,
        "band": badge,  # API compatibility
        "risk_level": risk_level,
        "reasons": reasons,
        "evidence": evidence,
        "is_mock": True,
        "details": {
            "age_years": age,
            "address": vendor.get("address", "N/A"),
            "state": vendor.get("state", "N/A"),
            "court_cases_count": len(court_cases),
            "missing_filings_count": missing_cnt,
            "adverse_media_count": len(adverse),
        },
    }


def check_vendor(query: str, gstin: Optional[str] = None, pan: Optional[str] = None) -> Dict[str, Any]:
    """Primary entry point for vendor verification. Returns score, badge, and reasons."""
    search_key = query or gstin or pan or ""
    vendor_rec = find_vendor_record(search_key)

    if vendor_rec:
        return calculate_vendor_trust_score(vendor_rec, provided_gstin=gstin)

    # If vendor is not in seeded mock database, evaluate based on GSTIN/PAN directly
    clean_query = search_key.strip()
    is_gst = gstin_valid(clean_query) or (gstin and gstin_valid(gstin))
    is_p = pan_valid(clean_query) or (pan and pan_valid(pan))

    synthetic_vendor = {
        "name": query or (clean_query if not is_gst else f"Vendor ({clean_query[:10]})"),
        "id": "unregistered_vendor",
        "gstin": clean_query if is_gst else (gstin or ""),
        "pan": clean_query if is_p else (pan or (extract_pan_from_gstin(clean_query) if is_gst else "")),
        "age_years": 1.0 if is_gst else 0.2,
        "address": "Unregistered / Unknown Address",
        "state": "Unknown",
        "filing_history": {"missing_filings_count": 0 if is_gst else 2, "delayed_filings_count": 0},
        "court_cases": [],
        "insolvency_proceedings": False,
        "adverse_media": [],
        "is_mock": True,
    }
    return calculate_vendor_trust_score(synthetic_vendor, provided_gstin=gstin or (clean_query if is_gst else None))
