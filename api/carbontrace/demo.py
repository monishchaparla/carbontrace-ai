"""Seed a database from cached benchmark outputs, without calling Gemini.

Used by scripts/seed_demo.py and, when CARBONTRACE_SEED_DEMO=1, by the API on a cold start.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from decimal import Decimal
from pathlib import Path

from carbontrace import store
from carbontrace.calc import calculate
from carbontrace.match import factor_table, to_factor
from carbontrace.pipeline import LineResult, PipelineResult, activity_amount
from carbontrace.schema import ExtractedDocument, Flag

ROOT = Path(__file__).resolve().parents[1]


def build(run: dict) -> PipelineResult:
    doc = ExtractedDocument.model_validate(run["document"])
    table = factor_table().set_index("factor_id", drop=False)
    lines = []
    for ln in run["lines"]:
        item = doc.line_items[ln["line_index"]]
        fid = ln.get("factor_id")
        row = table.loc[fid] if fid and fid in table.index else None
        factor = to_factor(row) if row is not None else None
        trace = ln.get("trace")
        if trace is None and factor is not None and ln.get("kg_co2e") is not None:
            try:  # deterministic replay of the calculation, no API call
                qty, unit, note = activity_amount(item, factor)
                trace = {**calculate(qty, unit, factor).trace, "derived_quantity": note, "match_method": ln.get("method")}
            except Exception:
                trace = None
        kg = ln.get("kg_co2e")
        lines.append(LineResult(
            line_index=ln["line_index"], description=item.description,
            scope=factor.scope if factor else None, factor_id=fid, factor_name=factor.name if factor else None,
            method=ln.get("method", ""), kg_co2e=Decimal(kg) if kg is not None else None, trace=trace,
            shortlist=ln.get("shortlist", []),
        ))
    return PipelineResult(doc, [Flag(**f) for f in run["flags"]], lines, run.get("model", ""), run.get("attempts", []))


def seed(conn: sqlite3.Connection) -> int:
    """Add every cached benchmark document not already present. Returns how many were added."""
    added = 0
    for f in sorted((ROOT / "evals" / "runs").glob("*.json")):
        run = json.loads(f.read_text(encoding="utf-8"))
        if run.get("error"):
            continue
        pdf = ROOT / "evals" / "docs" / f.name.removesuffix(".json")
        if not pdf.exists():
            continue
        sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        if store.find_by_hash(conn, sha):
            continue
        # Relative to api/, so the database works on any machine or server.
        doc_id = store.create_document(conn, pdf.name, "application/pdf", sha, pdf.relative_to(ROOT).as_posix())
        store.save_result(conn, doc_id, build(run))
        added += 1
    return added
