"""Load cached benchmark outputs into a SQLite DB so the UI has data without calling Gemini.

python scripts/seed_demo.py [db_path]      # default data/demo.db; safe to re-run
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from carbontrace import store  # noqa: E402
from carbontrace.calc import calculate  # noqa: E402
from carbontrace.match import factor_table, to_factor  # noqa: E402
from carbontrace.pipeline import LineResult, PipelineResult, activity_amount  # noqa: E402
from carbontrace.schema import ExtractedDocument, Flag  # noqa: E402


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
        ))
    return PipelineResult(doc, [Flag(**f) for f in run["flags"]], lines, run.get("model", ""), run.get("attempts", []))


def main() -> None:
    db = sys.argv[1] if len(sys.argv) > 1 else "data/demo.db"
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    conn = store.connect(db)
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
        doc_id = store.create_document(conn, pdf.name, "application/pdf", sha, str(pdf))
        store.save_result(conn, doc_id, build(run))
        added += 1
    print(f"seeded {added} document(s) into {db}")


if __name__ == "__main__":
    main()
