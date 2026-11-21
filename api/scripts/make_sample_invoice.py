"""Generate a fictional electricity bill PDF for testing extraction.

The utility and customer are invented; the layout mimics a typical Indian LT industrial bill.
Run: python scripts/make_sample_invoice.py [--mwh]
  --mwh prints the consumption unit as MWh by mistake, to exercise the review flag.
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

OUT_DIR = Path(__file__).resolve().parents[1] / "samples"


def make(path: Path, wrong_unit: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    y = h - 25 * mm
    c.setFont("Helvetica-Bold", 15)
    c.drawString(20 * mm, y, "Sahyadri Power Distribution Ltd (fictional)")
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, y - 6 * mm, "LT Industrial Electricity Bill  |  Sample document for software testing")
    y -= 20 * mm
    rows = [
        ("Consumer", "Acme Components Pvt Ltd, Plant 2, Chakan, Pune"),
        ("Consumer No.", "170012345678"),
        ("Bill No.", "SPDL/2026/09/48812"),
        ("Bill Date", "05-10-2026"),
        ("Billing Period", "01-09-2026 to 30-09-2026"),
        ("Tariff", "LT-V(B) Industrial"),
    ]
    for k, v in rows:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20 * mm, y, k)
        c.setFont("Helvetica", 10)
        c.drawString(60 * mm, y, v)
        y -= 6 * mm
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 10)
    for x, t in [(20, "Description"), (100, "Quantity"), (130, "Unit"), (160, "Amount (Rs)")]:
        c.drawString(x * mm, y, t)
    c.line(20 * mm, y - 2 * mm, 190 * mm, y - 2 * mm)
    y -= 8 * mm
    unit = "MWh" if wrong_unit else "kWh"
    lines = [
        ("Energy consumed (Present 284,150 - Previous 259,650)", "24500", unit, "232,750.00"),
        ("Fixed / demand charges (120 kVA)", "120", "kVA", "52,800.00"),
        ("Electricity duty", "", "", "17,456.25"),
        ("Fuel adjustment charge", "24500", "kWh", "8,330.00"),
    ]
    c.setFont("Helvetica", 10)
    for d, q, u, a in lines:
        c.drawString(20 * mm, y, d)
        c.drawRightString(118 * mm, y, q)
        c.drawString(130 * mm, y, u)
        c.drawRightString(185 * mm, y, a)
        y -= 7 * mm
    c.line(20 * mm, y + 3 * mm, 190 * mm, y + 3 * mm)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y - 3 * mm, "Total payable")
    c.drawRightString(185 * mm, y - 3 * mm, "3,11,336.25")
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, 15 * mm, "This is a computer-generated sample for software testing. Not a real bill.")
    c.showPage()
    c.save()
    return path


if __name__ == "__main__":
    wrong = "--mwh" in sys.argv
    out = make(OUT_DIR / ("sample_bill_wrong_unit.pdf" if wrong else "sample_bill.pdf"), wrong_unit=wrong)
    print(out)
