"""BizSim Executive Decision Report PDF Generator.

Produces a professional, publication-quality 1-page PDF summarizing the simulation scenario,
cascade event sequence, action comparison matrix, explicit assumptions, and recommended course.
"""

from __future__ import annotations

import io
from datetime import date
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_report(
    business_name: str = "Sharma Hardware and Electricals",
    scenario_desc: str = "Supplier A shipment delayed by 14 days (arriving Day 22 instead of Day 8)",
    cascade_events: Optional[List[Dict[str, Any]]] = None,
    actions_data: Optional[List[Dict[str, Any]]] = None,
    assumptions: Optional[List[str]] = None,
) -> io.BytesIO:
    """Generate a clean, structured 1-page PDF decision report."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=6,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155"),
    )
    cell_style = ParagraphStyle(
        "CellBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    badge_rec = ParagraphStyle(
        "BadgeRec",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#15803d"),
    )

    elements = []

    # 1. Header Banner
    header_data = [
        [
            Paragraph("<b>BIZSIM</b> &bull; Executive Decision Report", title_style),
            Paragraph(f"<b>Date:</b> {date.today().strftime('%d %b %Y')}<br/><b>Entity:</b> {business_name}<br/><b>Status:</b> Synthetic Demo", subtitle_style),
        ]
    ]
    header_table = Table(header_data, colWidths=[340, 180])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=8))

    # 2. Executive Situation Summary Box
    summary_text = (
        f"<b>Disruption Trigger:</b> {scenario_desc}.<br/>"
        "<b>Root Cause Mechanism:</b> Inventory buffer for Fans and Wiring is exhausted on <b>Day 10</b>. "
        "The Verma Contractors order (₹74,000) slips from Day 12 to Day 22, postponing receivable inflow. "
        "Opening cash (₹50,000) is depleted by recurring daily overheads, resulting in a <b>₹1,27,500 deficit on Day 23</b> "
        "and cascading failure of the Supplier C payment (₹70,000) on Day 25."
    )
    summary_box = Table(
        [[Paragraph(summary_text, body_style)]],
        colWidths=[520],
    )
    summary_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_box)
    elements.append(Spacer(1, 8))

    # 3. Cascade Impact Timeline
    elements.append(Paragraph("1. Simulated Cascade Sequence (30-Day Horizon)", section_style))
    if not cascade_events:
        cascade_events = [
            {"day": 8, "event": "Supplier A restock slips from Day 8 to Day 22", "severity": "Trigger"},
            {"day": 10, "event": "Fans and Wiring stockouts begin (Buffer depleted)", "severity": "Stockout"},
            {"day": 12, "event": "Verma Contractors delivery delayed by 10 days", "severity": "Delay"},
            {"day": 23, "event": "Cash deficit: Supplier A invoice (₹2,75,000) cannot be paid", "severity": "Critical"},
            {"day": 25, "event": "Supplier C payment (₹70,000) fails due to zero liquidity", "severity": "Critical"},
        ]

    event_rows = [
        [
            Paragraph("<b>Day</b>", cell_bold),
            Paragraph("<b>Operational / Financial Event</b>", cell_bold),
            Paragraph("<b>Impact Classification</b>", cell_bold),
        ]
    ]
    for ev in cascade_events:
        event_rows.append([
            Paragraph(f"Day {ev.get('day')}", cell_style),
            Paragraph(ev.get("event", ev.get("text", "")), cell_style),
            Paragraph(ev.get("severity", "Operational"), cell_style),
        ])

    event_table = Table(event_rows, colWidths=[55, 360, 105])
    event_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(event_table)
    elements.append(Spacer(1, 8))

    # 4. Action Comparison Matrix
    elements.append(Paragraph("2. Action Comparison Matrix & Risk Scoring", section_style))
    action_rows = [
        [
            Paragraph("<b>Action Strategy</b>", cell_bold),
            Paragraph("<b>Lowest Cash</b>", cell_bold),
            Paragraph("<b>First Gap</b>", cell_bold),
            Paragraph("<b>Risk Level</b>", cell_bold),
            Paragraph("<b>Key Trade-off / Feasibility</b>", cell_bold),
        ]
    ]

    default_actions = [
        {"name": "Do Nothing", "min_cash": "₹-1,27,500", "gap": "Day 23", "risk": "High (3 pts)", "tradeoff": "Two supplier defaults; business insolvency risk.", "suggested": False},
        {"name": "Ask Extension (15d)", "min_cash": "₹15,000", "gap": "None", "risk": "Low (1 pt)", "tradeoff": "Eliminates cash deficit; relies on Supplier A consent.", "suggested": False},
        {"name": "Early Discount (3%)", "min_cash": "₹-55,720", "gap": "Day 23", "risk": "Medium (2 pts)", "tradeoff": "Reduces margin by ₹2,220; deficit reduced but still fails.", "suggested": False},
        {"name": "Switch Supplier", "min_cash": "₹-83,500", "gap": "Day 3", "risk": "High (4 pts)", "tradeoff": "New distributor rated RED (score 28); 50% advance fails.", "suggested": False},
        {"name": "Extension + Discount (Combined)", "min_cash": "₹86,780", "gap": "None", "risk": "Low (1 pt)", "tradeoff": "Optimal liquidity cushion; protects all supplier obligations.", "suggested": True},
    ]

    for act in (actions_data or default_actions):
        label_p = Paragraph(f"<b>{act['name']}</b>" + (" <font color='#15803d'>[SUGGESTED]</font>" if act.get("suggested") else ""), cell_style)
        action_rows.append([
            label_p,
            Paragraph(str(act.get("min_cash", "N/A")), cell_style),
            Paragraph(str(act.get("gap", "None")), cell_style),
            Paragraph(str(act.get("risk", "Low")), cell_style),
            Paragraph(str(act.get("tradeoff", "")), cell_style),
        ])

    act_table = Table(action_rows, colWidths=[130, 75, 60, 75, 180])
    act_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 3.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#f0fdf4")),
    ]))
    elements.append(act_table)
    elements.append(Spacer(1, 8))

    # 5. Strategic Recommendation & Explicit Assumptions
    rec_text = (
        "<b>Recommended Decision:</b> Execute <b>Extension plus Early Discount (Combined Action)</b>. "
        "Formally request a 15-day invoice extension from Supplier A (postponing the ₹2,75,000 payable to Day 38) "
        "and offer Verma Contractors a 3% prompt-payment incentive upon delivery. This maintains a healthy minimum cash balance of ₹86,780.<br/>"
        "<b>AVOID:</b> Switching to the new distributor due to severe red-flag trust rating (Score 28/100, cheque bounce cases, and shell characteristics)."
    )
    rec_box = Table(
        [[Paragraph(rec_text, body_style)]],
        colWidths=[520],
    )
    rec_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ecfdf5")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(rec_box)
    elements.append(Spacer(1, 6))

    # Assumptions Footnote
    if not assumptions:
        assumptions = [
            "Baseline demand: Fans (4/day), Wiring (6/day), Switches (15/day). Fixed costs: ₹3,000/day + ₹1,800/day other supplies.",
            "Opening cash: ₹50,000. Supplier A invoice: ₹2,75,000 due Day 23. Supplier C payable: ₹70,000 due Day 25.",
            "Data disclosure: Numbers computed deterministically by BizSim Cascade Engine. Vendor metrics from regulatory mock signals.",
        ]

    assump_paras = [Paragraph(f"&bull; {a}", subtitle_style) for a in assumptions]
    elements.append(Paragraph("<b>Model Assumptions & Data Provenance:</b>", subtitle_style))
    for p in assump_paras:
        elements.append(p)

    doc.build(elements)
    buf.seek(0)
    return buf
