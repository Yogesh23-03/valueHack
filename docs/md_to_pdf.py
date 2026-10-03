"""Minimal Markdown -> PDF converter for the BizSim engineering report.

Used because the available LaTeX engine (MiKTeX) is missing packages, while
ReportLab is already a backend dependency. It handles the subset of Markdown
used in the report: headings, paragraphs, bullet/numbered lists, fenced code
blocks and pipe tables (rendered as monospaced preformatted text).

Usage:
    python docs/md_to_pdf.py docs/BizSim_Engineering_Report.md docs/BizSim_Engineering_Report.pdf
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer

MAX_CHARS_PER_LINE = 96


def inline(text: str) -> str:
    """Escape XML for ReportLab and convert common inline markers."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', text)
    return text


def wrap_table(block: list[str]) -> list[str]:
    """Render a pipe table as fixed-width text."""
    rows: list[list[str]] = []
    for line in block:
        if re.fullmatch(r"\|[\s:\-|]+\|", line.strip()):
            continue  # separator row
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append([re.sub(r"[*`]", "", c) for c in cells])
    if not rows:
        return []
    widths = [max(len(r[i]) if i < len(r) else 0 for r in rows) for i in range(max(len(r) for r in rows))]
    total = sum(widths) + 3 * (len(widths) - 1)
    if total > MAX_CHARS_PER_LINE:  # scale down wide tables
        factor = (MAX_CHARS_PER_LINE - 3 * (len(widths) - 1)) / sum(widths)
        widths = [max(6, int(w * factor)) for w in widths]
    out = []
    for idx, row in enumerate(rows):
        cells = [(row[i] if i < len(row) else "")[: widths[i]].ljust(widths[i]) for i in range(len(widths))]
        out.append(" | ".join(cells))
        if idx == 0:
            out.append("-+-".join("-" * w for w in widths))
    return out


def convert(md_path: Path, pdf_path: Path) -> None:
    styles = getSampleStyleSheet()
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9.5, leading=13, spaceAfter=5)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18, leading=22, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, leading=18, spaceBefore=10, spaceAfter=6)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=4)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=12, bulletIndent=3, spaceAfter=3)
    code = ParagraphStyle("Code", parent=styles["Code"], fontSize=7.4, leading=9, backColor="#F4F4F6")

    story: list = []
    lines = md_path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("```"):  # fenced code
            i += 1
            block = []
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i].rstrip())
                i += 1
            i += 1
            story.append(Spacer(1, 3))
            story.append(Preformatted("\n".join(block), code))
            story.append(Spacer(1, 5))
            continue

        if line.strip().startswith("|"):  # table
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].rstrip())
                i += 1
            rendered = wrap_table(block)
            if rendered:
                story.append(Spacer(1, 3))
                story.append(Preformatted("\n".join(rendered), code))
                story.append(Spacer(1, 5))
            continue

        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = inline(line[level:].strip())
            story.append(Paragraph(text, {1: h1, 2: h2}.get(level, h3)))
        elif re.match(r"^\s*[-*]\s+", line):
            story.append(Paragraph(inline(re.sub(r"^\s*[-*]\s+", "", line)), bullet, bulletText="•"))
        elif re.match(r"^\s*\d+\.\s+", line):
            num = re.match(r"^\s*(\d+)\.\s+", line).group(1)
            story.append(Paragraph(inline(re.sub(r"^\s*\d+\.\s+", "", line)), bullet, bulletText=f"{num}."))
        elif line.strip() in ("---", "***"):
            story.append(Spacer(1, 6))
        elif line.strip():
            story.append(Paragraph(inline(line.strip()), body))
        i += 1

    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=A4,
        leftMargin=16 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title="BizSim Engineering Report", author="Person 1",
    )
    doc.build(story)
    print(f"wrote {pdf_path} ({pdf_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
