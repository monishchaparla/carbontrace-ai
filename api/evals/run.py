"""Run the pipeline on the benchmark and score it against ground truth.

python -m evals.run            # process uncached docs (calls Gemini), then score
python -m evals.run --score    # score cached outputs only, no API calls
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from decimal import Decimal
from pathlib import Path

from carbontrace.calc import Factor
from carbontrace.extract import extract_file
from carbontrace.match import INDIA_GRID, factor_table
from carbontrace.pipeline import activity_amount, run
from carbontrace.schema import LineItem
from carbontrace.units import try_parse_unit

HERE = Path(__file__).resolve().parent
BASE = HERE / sys.argv[sys.argv.index("--set") + 1] if "--set" in sys.argv else HERE  # held-out sets: evals/<set>/
RUNS = BASE / "runs"
TOL = Decimal("0.001")  # 0.1% relative tolerance on quantities


def canonical(qty: str | None, unit: str | None):
    """(magnitude, base units) or None if unparseable."""
    if not qty or not unit:
        return None
    u = try_parse_unit(unit)
    if u is None:
        return None
    try:
        q = (Decimal(qty.replace(",", "")) * u).to_base_units()
    except Exception:
        return None
    return Decimal(str(q.magnitude)), str(q.units)


def close(a, b) -> bool:
    return a is not None and b is not None and a[1] == b[1] and abs(a[0] - b[0]) <= TOL * max(abs(b[0]), Decimal(1))


def factor_ok(hint: str, factor_id: str | None) -> bool:
    if not factor_id:
        return False
    if hint == "india grid electricity":
        return factor_id == INDIA_GRID
    row = factor_table().set_index("factor_id").loc[factor_id]
    name = row["name"].lower()
    if hint == "road freight tonne-km":
        return row["unit"] == "tonne.km" and "hgv" in name
    return hint in name


def factor_of(factor_id: str) -> Factor:
    row = factor_table().set_index("factor_id").loc[factor_id]
    return Factor(factor_id, row["source"], row["source_version"], int(row["scope"]), row["name"], row["unit"], Decimal(row["kgco2e_per_unit"]))


def process(doc_path: Path) -> dict:
    started = time.perf_counter()
    try:
        result = run(extract_file(doc_path))
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}", "seconds": round(time.perf_counter() - started, 1)}
    return {
        "seconds": round(time.perf_counter() - started, 1),
        "model": result.model,
        "attempts": result.attempts,
        "document": result.document.model_dump(mode="json"),
        "flags": [f.model_dump() for f in result.flags],
        "lines": [
            {"line_index": l.line_index, "factor_id": l.factor_id, "method": l.method, "shortlist": l.shortlist,
             "kg_co2e": str(l.kg_co2e) if l.kg_co2e is not None else None}
            for l in result.lines
        ],
    }


def score(gt: list[dict]) -> dict:
    found = total = spurious = errors = 0
    factor_hits = recall3_hits = factor_total = 0
    calc_errors: list[Decimal] = []
    flag_expected = flag_caught = clean_docs = clean_with_flags = 0
    seconds: list[float] = []
    per_doc = []

    for g in gt:
        out = json.loads((RUNS / f"{g['file']}.json").read_text(encoding="utf-8"))
        if "error" in out:
            errors += 1
            total += len(g["activities"])
            per_doc.append({"file": g["file"], "error": out["error"]})
            continue
        seconds.append(out["seconds"])
        items = out["document"]["line_items"]
        lines = {l["line_index"]: l for l in out["lines"]}
        activity_idx = [i for i, it in enumerate(items) if it["is_activity"]]
        used: set[int] = set()
        misses = []
        for a in g["activities"]:
            total += 1
            gold = canonical(a["quantity"], a["unit"])
            hit = None
            for i in activity_idx:
                if i in used:
                    continue
                q, u = items[i]["quantity"], items[i]["unit"]
                line = lines.get(i)
                if line and line["factor_id"] and items[i].get("distance_km"):
                    q, u, _ = activity_amount(LineItem(**items[i]), factor_of(line["factor_id"]))
                if close(canonical(q, u), gold):
                    hit = i
                    break
            if hit is None:
                misses.append(f"{a['quantity']} {a['unit']}")
                continue
            used.add(hit)
            found += 1
            line = lines.get(hit)
            if not line or not line["factor_id"]:
                continue
            factor_total += 1
            ok = factor_ok(a["expected_factor_hint"], line["factor_id"])
            factor_hits += ok
            recall3_hits += ok or any(factor_ok(a["expected_factor_hint"], fid) for fid in line["shortlist"][:3])
            if line["kg_co2e"]:
                f = factor_of(line["factor_id"])
                fu, gu = try_parse_unit(f.unit), try_parse_unit(a["unit"])
                if fu is not None and gu is not None and fu.dimensionality == gu.dimensionality:
                    gold_kg = Decimal(str((Decimal(a["quantity"]) * gu).to(fu).magnitude)) * f.kgco2e_per_unit
                    if gold_kg:
                        calc_errors.append(abs(Decimal(line["kg_co2e"]) - gold_kg) / gold_kg)
        spurious += len([i for i in activity_idx if i not in used])
        codes = {f["code"] for f in out["flags"]}
        for e in g["expected_flags"]:
            flag_expected += 1
            flag_caught += e in codes
        if not g["expected_flags"]:
            clean_docs += 1
            clean_with_flags += bool(codes)
        per_doc.append({"file": g["file"], "missed": misses, "flags": sorted(codes), "expected": g["expected_flags"],
                        "model": out["model"], "seconds": out["seconds"]})

    pct = lambda a, b: round(100 * a / b, 1) if b else None
    return {
        "documents": len(gt),
        "pipeline_errors": errors,
        "activity_lines": total,
        "extraction_recall_pct": pct(found, total),
        "spurious_activity_lines": spurious,
        "factor_accuracy_pct": pct(factor_hits, factor_total),
        "factor_recall_at_3_pct": pct(recall3_hits, factor_total),
        "calc_lines_within_0_5pct": pct(sum(e <= Decimal("0.005") for e in calc_errors), len(calc_errors)),
        "calc_lines_scored": len(calc_errors),
        "flag_recall": f"{flag_caught}/{flag_expected}",
        "clean_docs_with_any_flag": f"{clean_with_flags}/{clean_docs}",
        "median_seconds_per_doc": statistics.median(seconds) if seconds else None,
        "per_doc": per_doc,
    }


def main() -> None:
    gt = json.loads((BASE / "ground_truth.json").read_text(encoding="utf-8"))
    RUNS.mkdir(exist_ok=True)
    if "--score" not in sys.argv:
        for n, g in enumerate(gt, 1):
            cache = RUNS / f"{g['file']}.json"
            if cache.exists() and "error" not in json.loads(cache.read_text(encoding="utf-8")):
                continue
            out = process(BASE / "docs" / g["file"])
            cache.write_text(json.dumps(out, indent=1), encoding="utf-8")
            print(f"[{n}/{len(gt)}] {g['file']} {out.get('model', 'ERROR')} {out['seconds']}s", flush=True)
    result = score(gt)
    (BASE / "results.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "per_doc"}, indent=1))


if __name__ == "__main__":
    main()
