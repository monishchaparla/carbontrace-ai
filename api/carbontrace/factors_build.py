"""Build the unified emission-factor table from the official raw downloads.

Sources (files in data/raw/, downloaded from the publishers):
- EPA Supply Chain GHG Emission Factors v1.3.0, NAICS-6, kg CO2e per 2022 USD (spend-based, Scope 3).
- UK DESNZ GHG Conversion Factors 2026, flat file v1.2 (activity-based, Scopes 1-3).
- India CEA CO2 Baseline Database v22.0: all-India weighted average grid factor FY 2025-26,
  0.675 tCO2/MWh (1189.04 Mt / 1761.28 BU, incl. renewables), for Scope 2 electricity in India.

Output: data/factors.csv with one row per factor and its provenance.

Run: python -m carbontrace.factors_build
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pandas as pd

from carbontrace.units import try_parse_unit

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "factors.csv"

COLUMNS = [
    "factor_id", "source", "source_version", "scope", "category", "name",
    "unit", "kgco2e_per_unit", "region", "year", "notes",
]


def epa_factors() -> pd.DataFrame:
    df = pd.read_csv(RAW / "epa_useeio_v1.3.0_naics_co2e_usd2022.csv", dtype={"2017 NAICS Code": str})
    out = pd.DataFrame({
        "factor_id": "epa-sc-1.3:" + df["2017 NAICS Code"],
        "source": "US EPA Supply Chain GHG Emission Factors",
        "source_version": "v1.3.0 (USD 2022, with margins)",
        "scope": 3,
        "category": "Purchased goods and services (spend-based)",
        "name": df["2017 NAICS Title"],
        "unit": "USD",
        "kgco2e_per_unit": df["Supply Chain Emission Factors with Margins"].map(lambda v: str(Decimal(str(v)))),
        "region": "US",
        "year": 2022,
        "notes": "NAICS " + df["2017 NAICS Code"] + "; purchaser price in 2022 USD",
    })
    return out


def desnz_factors() -> pd.DataFrame:
    path = RAW / "desnz_2026_flat_revised.xlsx"
    raw = pd.read_excel(path, sheet_name="Factors by Category", header=None)
    header_row = raw.index[raw.iloc[:, 0].astype(str).str.strip() == "ID"][0]
    df = raw.iloc[header_row + 1:].copy()
    df.columns = [str(c).strip() for c in raw.iloc[header_row]]
    value_col = next(c for c in df.columns if c.startswith("GHG Conversion Factor"))
    df = df[df["GHG/Unit"].astype(str).str.strip() == "kg CO2e"]
    df = df[pd.to_numeric(df[value_col], errors="coerce").notna()]

    def label(row: pd.Series) -> str:
        parts = [row.get(k) for k in ("Level 2", "Level 3", "Level 4", "Column Text")]
        return ", ".join(str(p).strip() for p in parts if pd.notna(p) and str(p).strip())

    scope_num = df["Scope"].astype(str).str.extract(r"(\d)")[0]
    out = pd.DataFrame({
        "factor_id": "desnz-2026:" + df["ID"].astype(str),
        "source": "UK DESNZ GHG Conversion Factors",
        "source_version": "2026 flat file v1.2",
        "scope": pd.to_numeric(scope_num, errors="coerce"),
        "category": df["Level 1"].astype(str).str.strip(),
        "name": df.apply(label, axis=1),
        "unit": df["UOM"].astype(str).str.strip(),
        "kgco2e_per_unit": df[value_col].map(lambda v: str(Decimal(str(v)))),
        "region": "UK",
        "year": 2026,
        "notes": "",
    })
    return out.dropna(subset=["scope"]).astype({"scope": int})


def cea_factors() -> pd.DataFrame:
    return pd.DataFrame([{
        "factor_id": "cea-v22:india-grid-fy2025-26",
        "source": "India CEA CO2 Baseline Database",
        "source_version": "v22.0",
        "scope": 2,
        "category": "Electricity",
        "name": "Grid electricity, India, weighted average incl. renewables, FY 2025-26",
        "unit": "kWh",
        "kgco2e_per_unit": "0.675",
        "region": "IN",
        "year": 2026,
        "notes": "0.675 tCO2/MWh = 1189.04 Mt / 1761.28 BU; CO2 only, per CEA methodology",
    }])


def build() -> pd.DataFrame:
    df = pd.concat([cea_factors(), desnz_factors(), epa_factors()], ignore_index=True)[COLUMNS]
    df["calculable"] = df["unit"].map(lambda u: try_parse_unit(u) is not None)
    if df["factor_id"].duplicated().any():
        dupes = df.loc[df["factor_id"].duplicated(), "factor_id"].tolist()[:5]
        raise ValueError(f"Duplicate factor ids: {dupes}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    return df


if __name__ == "__main__":
    table = build()
    print(f"Wrote {len(table)} factors to {OUT}")
    print(table.groupby("source").agg(rows=("factor_id", "size"), calculable=("calculable", "sum")))
