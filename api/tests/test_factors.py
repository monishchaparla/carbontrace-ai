"""Sanity checks on the built factor table (run `python -m carbontrace.factors_build` first)."""

from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

FACTORS = Path(__file__).resolve().parents[1] / "data" / "factors.csv"

pytestmark = pytest.mark.skipif(not FACTORS.exists(), reason="factor table not built")


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return pd.read_csv(FACTORS, dtype={"kgco2e_per_unit": str})


def test_ids_unique(df):
    assert not df["factor_id"].duplicated().any()


def test_scopes_valid(df):
    assert set(df["scope"].unique()) <= {1, 2, 3}


def test_no_negative_factors(df):
    assert (df["kgco2e_per_unit"].map(Decimal) >= 0).all()


def test_all_three_sources_present(df):
    sources = set(df["source"])
    assert any("EPA" in s for s in sources)
    assert any("DESNZ" in s for s in sources)
    assert any("CEA" in s for s in sources)


def test_india_grid_matches_cea_v22(df):
    row = df[df["factor_id"] == "cea-v22:india-grid-fy2025-26"].iloc[0]
    assert Decimal(row["kgco2e_per_unit"]) == Decimal("0.675")
    assert row["unit"] == "kWh" and row["scope"] == 2


def test_diesel_per_litre_in_published_range(df):
    diesel = df[(df["source"].str.contains("DESNZ")) & (df["name"] == "Liquid fuels, Diesel (average biofuel blend)") & (df["unit"] == "litres")]
    value = Decimal(diesel.iloc[0]["kgco2e_per_unit"])
    assert Decimal("2.4") < value < Decimal("2.8")


def test_most_factors_are_calculable(df):
    assert df["calculable"].mean() > 0.99
