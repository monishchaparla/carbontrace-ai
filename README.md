# CarbonTrace AI

Audit-ready Scope 1, 2 and 3 carbon accounting from messy bills, invoices and manifests.

Upload a document, and CarbonTrace extracts each line item, maps it to an official emission factor,
and calculates tCO2e with deterministic Python math, keeping a trace back to the exact line on the
source document.

**Live demo:** https://carbontrace-three.vercel.app (API: https://carbontrace-api.vercel.app/health).
The demo is seeded with the 50 fictional benchmark documents. Uploading and marking documents
reviewed need a passcode, so visitors can browse without spending the extraction quota.

## How it works

1. **Extract** — Gemini reads the PDF or image into a strict Pydantic schema: quantity and unit exactly
   as printed, category, bounding box, confidence, and whether the line is an activity or a charge.
2. **Validate** — deterministic checks flag documents for human review: implausible price per kWh
   (kWh/MWh misprints), billing periods over 13 months, future dates, unknown units, repeated quantities.
3. **Match** — rules first (Indian grid electricity → CEA factor), then BM25 over factors with a
   compatible unit dimension, then Gemini picks from that shortlist only. Freight mode (road, rail, air,
   sea) is decided in code.
4. **Calculate** — `pint` and `Decimal`; the model never does arithmetic. Every result stores a trace.
5. **Audit** — an append-only audit log (enforced by SQLite triggers); flagged documents stay out of
   totals until a reviewer clears them.

## Benchmark (synthetic, fictional documents)

| Metric | Tuning set (50 docs) | Held-out set (50 docs) |
|---|---|---|
| Activity lines extracted | 100% | 100% |
| Charges wrongly counted as activities | 0 | 0 |
| Correct emission factor | 100% (77.6% before the freight-mode fix) | 100% |
| Calculations within 0.5% of ground truth | 100% | 100% |
| Planted problems flagged | 14 / 14 | 10 / 10 |
| Clean documents with a false flag | 0 / 37 | 0 / 41 |
| Median seconds per document | 9.1 | 8.4 |

Honest limits: both sets come from one generator (`api/evals/generate.py`), so they share layouts and
vocabulary; the held-out set uses a different seed and was never used for tuning. Real invoices are
messier, so expect lower numbers there. See `api/evals/` to reproduce (`python -m evals.run --set holdout`).

## Data sources

US EPA Supply Chain GHG Emission Factors v1.3.0, UK DESNZ GHG Conversion Factors 2026, and the India
CEA CO2 Baseline Database v22.0 (0.675 tCO2/MWh) — 3,639 factors with source and version on every row.
Details and licences in [`api/README.md`](api/README.md).

## Stack

| Layer | Choice |
|---|---|
| Extraction and matching | Gemini (structured output, model fallback chain), BM25 |
| Calculation | Python, `pint`, `Decimal` |
| Backend | FastAPI, SQLite (append-only audit log), deployed on Vercel |
| Frontend | Next.js 15, Tailwind CSS 4, Recharts, pdf.js (source-to-ledger audit view) |
| Tests | pytest (51 tests), benchmark runner |

## Repository layout

```
api/        Python engine, API, tests, evals
web/        Next.js frontend
DESIGN.md   Design system (colours, type, layout, components)
```

## Run locally

```bash
cd api && python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
python scripts/seed_demo.py data/demo.db
CARBONTRACE_DEV=1 CARBONTRACE_DB=data/demo.db uvicorn carbontrace.api:app --port 8000

cd web && npm install
CARBONTRACE_API_URL=http://127.0.0.1:8000 CARBONTRACE_API_KEY=dev npm run dev
```

Set `GEMINI_API_KEY` in `api/.env` to process new documents.

## Known limits

- The serverless demo keeps its database in `/tmp`; new uploads are temporary there. A hosted Postgres
  is the next step for persistence.
- One shared API key protects the API; there are no per-user accounts yet.
- Well-to-tank (upstream) factors are not added as separate Scope 3 lines yet.
