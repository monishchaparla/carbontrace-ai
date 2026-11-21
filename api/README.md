# CarbonTrace API and calculation engine

## Emission factor data

`python -m carbontrace.factors_build` turns the official downloads in `data/raw/` into one table,
`data/factors.csv` (3,639 factors), with the source and version on every row.

| Source | Version | Coverage | Licence |
|---|---|---|---|
| [US EPA Supply Chain GHG Emission Factors](https://catalog.data.gov/dataset/supply-chain-greenhouse-gas-emission-factors-v1-3-by-naics-6) | v1.3.0, NAICS-6, kg CO2e per 2022 USD | 1,016 spend-based factors (Scope 3) | US government data; see the dataset page |
| [UK DESNZ GHG Conversion Factors](https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026) | 2026 flat file v1.2 | 2,622 activity factors (Scopes 1 to 3) | Open Government Licence v3.0 |
| [India CEA CO2 Baseline Database](https://cea.nic.in/cdm-co2-baseline-database/) | v22.0 | All-India grid, FY 2025-26: 0.675 tCO2/MWh | Published by the Central Electricity Authority |

The CEA report PDF is not committed; download it from the CEA site to verify the figure
(1189.04 Mt CO2 / 1761.28 BU).

## Calculation rules

- The model extracts quantity, unit and category only. `carbontrace.calc.calculate` does all arithmetic
  with `Decimal` and `pint`.
- Units are parsed from invoice spellings (`units`, `Ltr`, `MT`, `tkm`, ...). Indian bills' "units"
  mean kWh, and "MT" means metric tonne.
- Converting between incompatible dimensions raises `UnitMismatch`.
- Spend-based factors need an explicit exchange rate from a documented source; there is no default.
- Every result includes a trace (factor id, version, converted quantity, formula) for audit replay.

## Extraction

`python -m carbontrace.extract samples/sample_bill.pdf` sends a PDF to Gemini with a strict
schema (`carbontrace/schema.py`) and returns line items with bounding boxes, then runs
deterministic checks (`carbontrace/validate.py`).

- Model fallback: `gemini-3.8-flash` → `gemini-3.6-flash` → `gemini-3.5-flash` → `gemini-3.1-flash-lite`
  on overload, timeout, quota or retirement. Override with `GEMINI_MODELS`.
- The model marks each line as an activity or a charge. Surcharges that reuse another line's
  consumption (fuel adjustment, duty) are not activities, which prevents double counting.
- Review flags: implausible price per kWh (kWh vs MWh misprints), periods over 13 months or reversed,
  future dates, unknown units, missing quantities, low confidence, repeated activity quantities.
- Set `GEMINI_API_KEY` in `api/.env` (git-ignored) or the environment.

`scripts/make_sample_invoice.py` creates a fictional bill (`--mwh` adds a unit misprint).

## Develop

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # or bin/pip on macOS/Linux
python -m carbontrace.factors_build
pytest
```
