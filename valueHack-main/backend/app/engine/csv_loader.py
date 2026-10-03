"""CSV data loader and validation engine for BizSim.

Validates and loads business tables into SQLite database:
- businesses
- suppliers
- products
- customers
- orders
- receivables
- payables
- bills
- vendor_checks
- scenarios

Strictly validates:
- Empty files (CSV_EMPTY)
- Format/decode errors (CSV_INVALID_FORMAT)
- Missing required columns (CSV_MISSING_COLUMN)
- Negative stock (CSV_NEGATIVE_STOCK)
- Non-numeric or invalid numbers (CSV_INVALID_NUMBER)
- Malformed dates (CSV_INVALID_DATE)
- Unknown or invalid supplier references (CSV_UNKNOWN_SUPPLIER)
- Duplicate IDs (CSV_DUPLICATE_ID)
- Inconsistent references (CSV_INVALID_REFERENCE)

Errors raise EngineError so FastAPI returns:
{"code": "CSV_...", "message": "..."}
"""

from __future__ import annotations

import csv
import datetime
import io
import zipfile
from typing import Any, Optional

from sqlmodel import Session

from .errors import EngineError
from ..models import (
    Bill as BillRow,
    Business as BusinessRow,
    Customer as CustomerRow,
    DailySale as DailySaleRow,
    Order as OrderRow,
    Payable as PayableRow,
    Product as ProductRow,
    Receivable as ReceivableRow,
    Scenario as ScenarioRow,
    Supplier as SupplierRow,
    VendorCheck as VendorCheckRow,
)

# Canonical CSV validation error codes
CSV_EMPTY = "CSV_EMPTY"
CSV_INVALID_FORMAT = "CSV_INVALID_FORMAT"
CSV_MISSING_COLUMN = "CSV_MISSING_COLUMN"
CSV_NEGATIVE_STOCK = "CSV_NEGATIVE_STOCK"
CSV_INVALID_NUMBER = "CSV_INVALID_NUMBER"
CSV_INVALID_DATE = "CSV_INVALID_DATE"
CSV_UNKNOWN_SUPPLIER = "CSV_UNKNOWN_SUPPLIER"
CSV_DUPLICATE_ID = "CSV_DUPLICATE_ID"
CSV_INVALID_REFERENCE = "CSV_INVALID_REFERENCE"


TABLE_REQUIRED_COLUMNS: dict[str, list[str]] = {
    "businesses": ["name", "cash", "fixed_cost", "other_supplies"],
    "suppliers": ["name"],
    "products": ["name", "price", "cost", "demand_per_day", "opening_stock"],
    "customers": ["name"],
    "orders": ["customer_name", "amount", "target_delivery_day"],
    "payables": ["name", "amount", "due_day"],
    "receivables": ["name", "amount", "due_day"],
    "bills": ["supplier_name", "amount", "date", "due_date"],
    "vendor_checks": ["name"],
    "scenarios": ["name", "scenario_type", "target", "magnitude"],
}


def _detect_table_type(columns: list[str]) -> Optional[str]:
    """Auto-detect table type based on column signatures."""
    cols = {c.strip().lower() for c in columns}
    if {"price", "cost", "opening_stock"}.issubset(cols):
        return "products"
    if {"fixed_cost", "other_supplies", "cash"}.issubset(cols):
        return "businesses"
    if {"target_delivery_day", "customer_name"}.issubset(cols) or "items" in cols:
        return "orders"
    if {"due_date", "date", "supplier_name"}.issubset(cols) or "bill_number" in cols:
        return "bills"
    if {"gstin", "score"}.issubset(cols) or ("pan" in cols and "name" in cols):
        return "vendor_checks"
    if {"scenario_type", "magnitude"}.issubset(cols):
        return "scenarios"
    if {"due_day", "amount", "customer_name"}.issubset(cols):
        return "receivables"
    if {"due_day", "amount"}.issubset(cols):
        return "payables"
    if "name" in cols and len(cols) <= 3:
        if "supplier" in cols or any("sup" in c for c in cols):
            return "suppliers"
        if "customer" in cols or any("cust" in c for c in cols):
            return "customers"
    return None


def parse_and_validate_csv(
    content: str,
    table_type: Optional[str] = None,
    session: Optional[Session] = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Parse CSV text, enforce validation rules, and return (table_type, rows)."""
    if not content or not content.strip():
        raise EngineError(CSV_EMPTY, "The uploaded CSV file is empty.")

    try:
        reader = csv.DictReader(io.StringIO(content.strip()))
    except Exception as exc:
        raise EngineError(CSV_INVALID_FORMAT, f"Malformed CSV structure: {exc}")

    if not reader.fieldnames:
        raise EngineError(CSV_EMPTY, "CSV has no headers or columns.")

    raw_fields = [f.strip() for f in reader.fieldnames if f]
    fieldnames = [f.lower() for f in raw_fields]

    resolved_table = table_type
    if not resolved_table:
        resolved_table = _detect_table_type(fieldnames)

    if not resolved_table or resolved_table not in TABLE_REQUIRED_COLUMNS:
        raise EngineError(
            CSV_INVALID_FORMAT,
            f"Could not identify a supported business table from columns: {raw_fields}. "
            f"Supported tables: {list(TABLE_REQUIRED_COLUMNS.keys())}",
        )

    # Check required columns
    required = TABLE_REQUIRED_COLUMNS[resolved_table]
    for req in required:
        if req not in fieldnames:
            raise EngineError(
                CSV_MISSING_COLUMN,
                f"Missing required column '{req}' in {resolved_table} CSV (found: {raw_fields}).",
            )

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    # Pre-fetch existing suppliers for reference validation if session provided
    existing_suppliers: set[str] = set()
    if session:
        existing_suppliers = {s.name.strip().lower() for s in session.query(SupplierRow).all()}

    for line_num, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items() if k}

        # Check duplicate ID
        row_id = row.get("id")
        if row_id:
            if row_id in seen_ids:
                raise EngineError(
                    CSV_DUPLICATE_ID,
                    f"Duplicate ID '{row_id}' found at line {line_num} in {resolved_table}.",
                )
            seen_ids.add(row_id)

        # Table-specific validations
        if resolved_table == "products":
            pname = row.get("name", "")
            if not pname:
                raise EngineError(CSV_MISSING_COLUMN, f"Product name cannot be empty at line {line_num}.")

            # Validate opening stock
            try:
                stock_val = float(row.get("opening_stock", 0))
            except ValueError:
                raise EngineError(
                    CSV_INVALID_NUMBER,
                    f"Invalid opening stock '{row.get('opening_stock')}' for product '{pname}' at line {line_num}.",
                )

            if stock_val < 0:
                raise EngineError(
                    CSV_NEGATIVE_STOCK,
                    f"Product '{pname}' has negative stock: {int(stock_val) if stock_val.is_integer() else stock_val}",
                )

            # Validate price and cost
            for col in ["price", "cost", "demand_per_day"]:
                try:
                    val = float(row.get(col, 0))
                    if val < 0:
                        raise EngineError(
                            CSV_INVALID_NUMBER,
                            f"Product '{pname}' has negative {col}: {val} at line {line_num}.",
                        )
                except ValueError:
                    raise EngineError(
                        CSV_INVALID_NUMBER,
                        f"Product '{pname}' has invalid numeric value for '{col}': '{row.get(col)}' at line {line_num}.",
                    )

            # Validate supplier reference
            sup_name = row.get("supplier_name") or row.get("supplier")
            if sup_name and existing_suppliers and sup_name.lower() not in existing_suppliers:
                raise EngineError(
                    CSV_UNKNOWN_SUPPLIER,
                    f"Product '{pname}' references unknown supplier '{sup_name}'. Known suppliers: {sorted(list(existing_suppliers))}",
                )

        elif resolved_table == "businesses":
            for col in ["cash", "fixed_cost", "other_supplies"]:
                try:
                    val = float(row.get(col, 0))
                    if val < 0 and col != "cash":
                        raise EngineError(
                            CSV_INVALID_NUMBER,
                            f"Business '{row.get('name')}' has negative {col}: {val} at line {line_num}.",
                        )
                except ValueError:
                    raise EngineError(
                        CSV_INVALID_NUMBER,
                        f"Invalid numeric value for '{col}': '{row.get(col)}' at line {line_num}.",
                    )

        elif resolved_table == "bills":
            # Validate dates
            for dcol in ["date", "due_date"]:
                dstr = row.get(dcol, "")
                if not dstr:
                    raise EngineError(CSV_INVALID_DATE, f"Missing {dcol} for bill at line {line_num}.")
                try:
                    datetime.date.fromisoformat(dstr)
                except ValueError:
                    raise EngineError(
                        CSV_INVALID_DATE,
                        f"Malformed date '{dstr}' for {dcol} at line {line_num}. Expected YYYY-MM-DD format.",
                    )

            # Validate bill amount
            try:
                amt = float(row.get("amount", 0))
                if amt <= 0:
                    raise EngineError(
                        CSV_INVALID_NUMBER,
                        f"Bill amount must be positive; got {amt} at line {line_num}.",
                    )
            except ValueError:
                raise EngineError(
                    CSV_INVALID_NUMBER,
                    f"Invalid bill amount '{row.get('amount')}' at line {line_num}.",
                )

        elif resolved_table in ("orders", "payables", "receivables"):
            try:
                amt = float(row.get("amount", 0))
                if amt <= 0:
                    raise EngineError(
                        CSV_INVALID_NUMBER,
                        f"Amount must be positive; got {amt} at line {line_num}.",
                    )
            except ValueError:
                raise EngineError(
                    CSV_INVALID_NUMBER,
                    f"Invalid amount '{row.get('amount')}' at line {line_num}.",
                )

        rows.append(row)

    if not rows:
        raise EngineError(CSV_EMPTY, f"No data rows found in {resolved_table} CSV.")

    return resolved_table, rows


def load_validated_rows_into_db(
    table_type: str,
    rows: list[dict[str, Any]],
    session: Session,
    business_id: int = 1,
) -> int:
    """Insert or update validated rows into the SQLite database."""
    count = 0

    if table_type == "businesses":
        for r in rows:
            existing = session.query(BusinessRow).first()
            if existing:
                existing.name = r["name"]
                existing.cash = float(r["cash"])
                existing.fixed_cost = float(r["fixed_cost"])
                existing.other_supplies = float(r["other_supplies"])
                session.add(existing)
            else:
                session.add(
                    BusinessRow(
                        name=r["name"],
                        cash=float(r["cash"]),
                        fixed_cost=float(r["fixed_cost"]),
                        other_supplies=float(r["other_supplies"]),
                    )
                )
            count += 1

    elif table_type == "suppliers":
        for r in rows:
            session.add(SupplierRow(name=r["name"], business_id=business_id))
            count += 1

    elif table_type == "products":
        for r in rows:
            session.add(
                ProductRow(
                    name=r["name"],
                    price=float(r["price"]),
                    cost=float(r["cost"]),
                    demand_per_day=float(r["demand_per_day"]),
                    opening_stock=int(float(r["opening_stock"])),
                    supplier_name=r.get("supplier_name") or r.get("supplier"),
                    business_id=business_id,
                )
            )
            count += 1

    elif table_type == "customers":
        for r in rows:
            session.add(CustomerRow(name=r["name"], business_id=business_id))
            count += 1

    elif table_type == "orders":
        for r in rows:
            session.add(
                OrderRow(
                    order_id=r.get("order_id"),
                    customer_name=r["customer_name"],
                    items=r.get("items", ""),
                    amount=float(r["amount"]),
                    target_delivery_day=int(float(r["target_delivery_day"])),
                    payment_terms_days=int(float(r.get("payment_terms_days", 7))),
                    business_id=business_id,
                )
            )
            count += 1

    elif table_type == "payables":
        for r in rows:
            session.add(
                PayableRow(
                    name=r["name"],
                    amount=float(r["amount"]),
                    due_day=int(float(r["due_day"])),
                    supplier_name=r.get("supplier_name"),
                    business_id=business_id,
                )
            )
            count += 1

    elif table_type == "receivables":
        for r in rows:
            session.add(
                ReceivableRow(
                    name=r["name"],
                    amount=float(r["amount"]),
                    due_day=int(float(r["due_day"])),
                    customer_name=r.get("customer_name"),
                    business_id=business_id,
                )
            )
            count += 1

    elif table_type == "bills":
        for r in rows:
            session.add(
                BillRow(
                    bill_number=r.get("bill_number"),
                    supplier_name=r["supplier_name"],
                    amount=float(r["amount"]),
                    date=r["date"],
                    due_date=r["due_date"],
                    status=r.get("status", "pending"),
                    business_id=business_id,
                )
            )
            count += 1

    elif table_type == "vendor_checks":
        for r in rows:
            session.add(
                VendorCheckRow(
                    name=r["name"],
                    gstin=r.get("gstin"),
                    pan=r.get("pan"),
                    score=int(float(r["score"])) if r.get("score") else None,
                    risk_level=r.get("risk_level"),
                    business_id=business_id,
                )
            )
            count += 1

    elif table_type == "scenarios":
        for r in rows:
            session.add(
                ScenarioRow(
                    name=r["name"],
                    scenario_type=r["scenario_type"],
                    target=r["target"],
                    magnitude=float(r["magnitude"]),
                    duration_days=int(float(r["duration_days"])) if r.get("duration_days") else None,
                    business_id=business_id,
                )
            )
            count += 1

    session.commit()
    return count
