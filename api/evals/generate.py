"""Generate a synthetic, fictional benchmark of 50 business PDFs with exact ground truth.

Run: python evals/generate.py   (from api/, using the venv python)
Writes evals/docs/doc_001.pdf ... doc_050.pdf and evals/ground_truth.json. Deterministic (fixed seed).
All companies are invented; every page footer says it is a sample for software testing.
"""

from __future__ import annotations

import json
import random
import re
from calendar import monthrange
from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
DOCS = HERE / "docs"
FOOTER = "Sample document for software testing. Fictional - not a real bill or invoice."

FONTS = {"Helvetica": "Helvetica-Bold", "Times-Roman": "Times-Bold", "Courier": "Courier-Bold"}
COL_ORDERS = [
    ["Description", "Quantity", "Unit", "Amount"],
    ["Description", "Unit", "Quantity", "Amount"],
    ["Quantity", "Unit", "Description", "Amount"],
    ["Description", "Amount", "Quantity", "Unit"],
]
COL_WIDTH_MM = {"Description": 88, "Quantity": 24, "Unit": 18, "Amount": 32}
LABELS = [
    {"Description": "Description", "Quantity": "Quantity", "Unit": "Unit", "Amount": "Amount (Rs)"},
    {"Description": "Particulars", "Quantity": "Qty", "Unit": "UoM", "Amount": "Value (INR)"},
]

UTILITIES = ["Sahyadri Power Distribution Ltd", "Kaveri Vidyut Nigam", "Narmada Urja Vitaran",
             "Himgiri Power Co", "Deccan Grid Services", "Malwa Electric Supply Ltd", "Thar Urja Ltd"]
FUEL_SELLERS = ["Rajmarg Fuels", "Sagarkinara Petro Station", "Vindhya Energy Retail",
                "Gomti Fuel Point", "Neelgiri Petro Hub", "Aravali Fuel Stop"]
HAULIERS = ["Trishul Roadlines", "Ganga Carriers", "Pinaka Logistics", "Sundarban Transport Co", "Kesari Freight Movers"]
GAS_SELLERS = ["Tarang Gas Agency", "Aranya City Gas", "Meghdoot Gas Supply"]
CUSTOMERS = ["Acme Components Pvt Ltd, Chakan, Pune", "Lotus Textiles Ltd, Surat", "Orchid Foods Pvt Ltd, Hosur",
             "Zenith Castings Pvt Ltd, Rajkot", "Banyan Plastics Ltd, Noida", "Indigo Packaging Co, Vapi"]
# Approximate road distances in km between invented-shipper routes (real cities only).
ROUTES = [("Pune", "Chennai", 1180), ("Mumbai", "Ahmedabad", 530), ("Delhi", "Jaipur", 280), ("Surat", "Indore", 450),
          ("Chennai", "Bengaluru", 350), ("Kolkata", "Patna", 580), ("Nagpur", "Hyderabad", 500),
          ("Ludhiana", "Delhi", 310), ("Coimbatore", "Kochi", 190), ("Lucknow", "Kanpur", 90)]


# ---------- formatting helpers ----------

def indian(n: int) -> str:
    """1245000 -> '12,45,000'."""
    s = str(n)
    return s if len(s) <= 3 else re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", s[:-3]) + "," + s[-3:]


def money(x: float) -> str:
    whole, frac = f"{x:.2f}".split(".")
    return f"{indian(int(whole))}.{frac}"


def pdate(rng: random.Random, d: date) -> str:
    return d.strftime(rng.choice(["%d-%m-%Y", "%d %b %Y", "%d/%m/%Y"]))


def row(desc: str, qty: str = "", unit: str = "", amount: float = 0.0) -> dict:
    return {"Description": desc, "Quantity": qty, "Unit": unit, "Amount": money(amount), "_amt": amount}


def activity(qty: int | str, unit: str, category: str, material: str | None, hint: str) -> dict:
    return {"quantity": str(qty), "unit": unit, "category": category, "fuel_or_material": material,
            "expected_factor_hint": hint, "kg_co2e_hint": None}


def truth(doc_type: str, start: date, end: date, activities: list, charges: int, flags: list | None = None) -> dict:
    return {"doc_type": doc_type, "currency": "INR", "country": "IN", "period_start": start.isoformat(),
            "period_end": end.isoformat(), "activities": activities, "charges": charges, "expected_flags": flags or []}


# ---------- document builders: each returns (spec for rendering, ground truth) ----------

def electricity(rng, mwh=False, long_period=False, indian_fmt=False):
    kwh = 124500 if indian_fmt else rng.randrange(3000, 180000, 50)
    unit = "MWh" if mwh else rng.choice(["kWh", "units", "KWH"])
    kva = rng.randrange(30, 400, 10)
    if long_period:
        start, end = date(2025, 11, 1), date(2026, 12, 31)
    else:
        m = rng.randint(1, 11)
        start, end = date(2026, m, 1), date(2026, m, monthrange(2026, m)[1])
    energy = kwh * rng.uniform(7.5, 9.5)
    rows = [row("Energy consumed", indian(kwh) if indian_fmt else str(kwh), unit, energy),
            row(f"Fixed / demand charges ({kva} kVA)", str(kva), "kVA", kva * rng.uniform(300, 450)),
            row("Electricity duty", amount=energy * 0.075),
            row("Fuel adjustment charge", str(kwh), unit, kwh * rng.uniform(0.3, 0.6))]
    if rng.random() < 0.4:
        rows.append(row("Meter rent", amount=rng.choice([150, 300, 450])))
    meta = [("Consumer", rng.choice(CUSTOMERS)), ("Consumer No.", str(rng.randrange(10**11, 10**12))),
            ("Bill No.", f"BL/2026/{rng.randint(10000, 99999)}"), ("Bill Date", pdate(rng, date(2026, 12, 15) if long_period else end.replace(day=28))),
            ("Billing Period", f"{pdate(rng, start)} to {pdate(rng, end)}"), ("Tariff", rng.choice(["LT-V(B) Industrial", "HT-I Industrial", "LT-II Commercial"]))]
    spec = {"supplier": rng.choice(UTILITIES), "subtitle": "Electricity Bill", "meta": meta, "rows": rows, "total_label": "Total payable"}
    flags = ["unit_suspect"] if mwh else ["period_too_long"] if long_period else []
    return spec, truth("electricity_bill", start, end, [activity(kwh, unit, "electricity", None, "india grid electricity")], len(rows) - 1, flags)


def fuel(rng, grey=False):
    kind = rng.choice(["diesel", "petrol"])
    litres = rng.choice([rng.randrange(40, 2500), round(rng.uniform(40, 900), 1)])
    unit = rng.choice(["Ltr", "L", "litres"])
    rate = rng.uniform(88, 98) if kind == "diesel" else rng.uniform(100, 106)
    base = litres * rate
    d = date(2026, rng.randint(1, 12), rng.randint(1, 28))
    rows = [row(f"{'High speed diesel' if kind == 'diesel' else 'Motor spirit (petrol)'}", str(litres), unit, base),
            row("CGST @ 9%", amount=base * 0.09), row("SGST @ 9%", amount=base * 0.09)]
    if rng.random() < 0.4:
        rows.append(row("Delivery charge", amount=rng.choice([250, 400, 600])))
    meta = [("Customer", rng.choice(CUSTOMERS)), ("Invoice No.", f"FU-{rng.randint(1000, 99999)}"), ("Date", pdate(rng, d)),
            ("Vehicle / Site", rng.choice(["Fleet depot", "Genset yard", "MH12 XX 0000", "Plant DG set"]))]
    spec = {"supplier": rng.choice(FUEL_SELLERS), "subtitle": rng.choice(["Fuel Purchase Invoice", "Fuel Receipt"]), "meta": meta,
            "rows": rows, "total_label": "Invoice total", "grey_row": 0 if grey else None}
    return spec, truth("fuel_receipt", d, d, [activity(litres, unit, "fuel", kind, kind)], len(rows) - 1)


def freight(rng, explicit_tkm: bool, two_page=False):
    origin, dest, km = rng.choice(ROUTES)
    tonnes = rng.randint(5, 30)
    d = date(2026, rng.randint(1, 12), rng.randint(1, 28))
    if explicit_tkm:
        act = row(f"Road freight {origin} to {dest}", str(tonnes * km), "tkm", tonnes * km * rng.uniform(2.2, 3.2))
    else:
        act = row(f"Freight {origin} to {dest}, {tonnes} MT x {km} km", str(tonnes), "MT", tonnes * km * rng.uniform(2.2, 3.2))
    rows = [act, row("Loading / unloading", amount=rng.choice([1500, 2500, 4000])), row("GST @ 5%", amount=act["_amt"] * 0.05)]
    if rng.random() < 0.5:
        rows.insert(1, row("Fuel surcharge", amount=act["_amt"] * 0.06))
    meta = [("Consignor", rng.choice(CUSTOMERS)), ("Invoice No.", f"RF/{rng.randint(1000, 99999)}"), ("Date", pdate(rng, d)),
            ("From", origin), ("To", dest), ("LR No.", str(rng.randint(100000, 999999)))]
    spec = {"supplier": rng.choice(HAULIERS), "subtitle": "Freight Invoice", "meta": meta, "rows": rows,
            "total_label": "Grand total", "two_page": two_page}
    return spec, truth("freight_invoice", d, d, [activity(tonnes * km, "tkm", "freight", None, "road freight tonne-km")], len(rows) - 1)


def gas(rng):
    lpg = rng.random() < 0.6
    qty, unit = (rng.choice([19 * n for n in range(5, 60)] + [rng.randrange(300, 3000, 50)]), "kg") if lpg else (rng.randrange(800, 9000, 25), "SCM")
    d = date(2026, rng.randint(1, 12), rng.randint(1, 28))
    base = qty * (rng.uniform(85, 110) if lpg else rng.uniform(48, 62))
    rows = [row("Commercial LPG supply" if lpg else "Piped natural gas supply", str(qty), unit, base),
            row("GST @ 5%" if lpg else "GST @ 18%", amount=base * (0.05 if lpg else 0.18))]
    if rng.random() < 0.6:
        rows.append(row("Delivery / regulator rent", amount=rng.choice([200, 350, 500])))
    meta = [("Customer", rng.choice(CUSTOMERS)), ("Invoice No.", f"GS-{rng.randint(1000, 99999)}"), ("Invoice Date", pdate(rng, d))]
    spec = {"supplier": rng.choice(GAS_SELLERS), "subtitle": "Gas Supply Invoice", "meta": meta, "rows": rows, "total_label": "Total due"}
    hint = "lpg" if lpg else "natural gas"
    return spec, truth("supplier_invoice", d, d, [activity(qty, unit, "fuel", hint, hint)], len(rows) - 1)


# ---------- rendering (layout is randomised per document) ----------

def render(path: Path, spec: dict, rng: random.Random) -> None:
    font = rng.choice(list(FONTS))
    bold = FONTS[font]
    size = rng.choice([8, 9, 10])
    if font == "Courier":
        size = min(size, 9)
    order = rng.choice(COL_ORDERS)
    labels = rng.choice(LABELS)
    inline_meta = rng.random() < 0.5
    meta_below = rng.random() < 0.25
    centered = rng.random() < 0.4
    x0 = 20 * mm
    xs, x = {}, x0
    for col in order:
        xs[col] = x
        x += COL_WIDTH_MM[col] * mm

    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4

    def footer():
        c.setFillGray(0)
        c.setFont(font, 8)
        c.drawString(x0, 15 * mm, FOOTER)

    def title(y, subtitle):
        c.setFont(bold, size + 6)
        (c.drawCentredString(w / 2, y, f"{spec['supplier']} (fictional)") if centered
         else c.drawString(x0, y, f"{spec['supplier']} (fictional)"))
        c.setFont(font, size)
        (c.drawCentredString(w / 2, y - 6 * mm, subtitle) if centered else c.drawString(x0, y - 6 * mm, subtitle))
        return y - 18 * mm

    def meta(y):
        for k, v in spec["meta"]:
            c.setFont(bold, size)
            if inline_meta:
                c.drawString(x0, y, f"{k}: ")
                c.setFont(font, size)
                c.drawString(x0 + stringWidth(f"{k}: ", bold, size), y, v)
            else:
                c.drawString(x0, y, k)
                c.setFont(font, size)
                c.drawString(x0 + 38 * mm, y, v)
            y -= 6 * mm
        return y - 4 * mm

    def table(y):
        c.setFont(bold, size)
        for col in order:
            right = col in ("Quantity", "Amount")
            cx = xs[col] + COL_WIDTH_MM[col] * mm - 2 * mm if right else xs[col]
            (c.drawRightString if right else c.drawString)(cx, y, labels[col])
        c.line(x0, y - 2 * mm, x0 + sum(COL_WIDTH_MM.values()) * mm, y - 2 * mm)
        y -= 8 * mm
        for i, r in enumerate(spec["rows"]):
            assert stringWidth(r["Description"], font, size) < (COL_WIDTH_MM["Description"] - 2) * mm, r["Description"]
            for col in order:
                c.setFont(font, size)
                c.setFillGray(0.8 if col == "Quantity" and spec.get("grey_row") == i else 0)
                right = col in ("Quantity", "Amount")
                cx = xs[col] + COL_WIDTH_MM[col] * mm - 2 * mm if right else xs[col]
                (c.drawRightString if right else c.drawString)(cx, y, r[col])
            c.setFillGray(0)
            y -= 7 * mm
        total = money(sum(r["_amt"] for r in spec["rows"]))
        c.line(x0, y + 3 * mm, x0 + sum(COL_WIDTH_MM.values()) * mm, y + 3 * mm)
        c.setFont(bold, size + 1)
        c.drawString(x0, y - 3 * mm, spec["total_label"])
        c.drawRightString(xs["Amount"] + COL_WIDTH_MM["Amount"] * mm - 2 * mm, y - 3 * mm, total)
        return y - 14 * mm

    y = title(h - 25 * mm, spec["subtitle"])
    if spec.get("two_page"):
        y = meta(y)
        c.setFont(font, size)
        c.drawString(x0, y, "Itemised charges are shown on page 2 of 2.")
        footer()
        c.showPage()
        c.setFont(bold, size + 2)
        c.drawString(x0, h - 25 * mm, f"{spec['supplier']} (fictional) - Invoice (continued), page 2 of 2")
        table(h - 40 * mm)
    elif meta_below:
        y = table(y)
        meta(y)
    else:
        table(meta(y))
    footer()
    c.showPage()
    c.save()


def main() -> None:
    rng = random.Random(2026)
    DOCS.mkdir(parents=True, exist_ok=True)
    mwh_idx = set(rng.sample(range(18), 3))
    builders = (
        [lambda i=i: electricity(rng, mwh=i in mwh_idx) for i in range(18)]
        + [lambda: fuel(rng) for _ in range(12)]
        + [lambda e=e: freight(rng, explicit_tkm=e) for e in [True] * 5 + [False] * 5]
        + [lambda: gas(rng) for _ in range(6)]
        + [lambda: electricity(rng, long_period=True), lambda: fuel(rng, grey=True),
           lambda: freight(rng, explicit_tkm=True, two_page=True), lambda: electricity(rng, indian_fmt=True)]
    )
    rng.shuffle(builders)
    entries = []
    for n, build in enumerate(builders, 1):
        spec, gt = build()
        name = f"doc_{n:03d}.pdf"
        render(DOCS / name, spec, rng)
        entries.append({"file": name, **gt})
    (HERE / "ground_truth.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"wrote {len(entries)} docs to {DOCS}")


if __name__ == "__main__":
    main()
