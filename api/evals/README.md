# Extraction benchmark

50 synthetic, fictional business PDFs (`docs/doc_001.pdf` ... `doc_050.pdf`) with exact ground truth in `ground_truth.json`.
All companies are invented; every page footer reads "Sample document for software testing". No real names or logos.

Mix: 20 Indian electricity bills (3 misprint the unit as MWh, 1 spans 14 months, 1 uses "1,24,500" grouping),
13 diesel/petrol receipts (1 has low-contrast grey quantity), 11 road freight invoices (1 has its line on page 2),
6 LPG / natural gas invoices. Layouts, fonts and column order vary. Files are shuffled so numbering does not reveal type.

Ground truth per doc: `doc_type`, `period_start/end`, `activities` (quantity as digits, unit as printed, category,
factor hint), `charges` (count of non-activity lines) and `expected_flags` (`unit_suspect`, `period_too_long`).
Freight quantities are in `tkm` (weight x distance when printed separately). The one 14-month bill starts 2025-11-01.

Regenerate (deterministic, fixed seed), from `api/`:

    .venv/Scripts/python evals/generate.py
