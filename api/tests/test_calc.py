from decimal import Decimal

import pytest

from carbontrace.calc import Factor, MissingExchangeRate, UnitMismatch, calculate
from carbontrace.units import UnknownUnit

GRID_IN = Factor("cea-v22:india-grid-fy2025-26", "CEA", "v22.0", 2, "India grid", "kWh", Decimal("0.675"))
DIESEL = Factor("desnz-2026:diesel", "DESNZ", "2026", 1, "Diesel (average biofuel blend)", "litres", Decimal("2.57082"))
STEEL_SPEND = Factor("epa-sc-1.3:331110", "EPA", "v1.3.0", 3, "Iron and steel mills", "USD", Decimal("1.200"))
FREIGHT = Factor("desnz-2026:hgv", "DESNZ", "2026", 3, "HGV, average laden", "tonne.km", Decimal("0.10"))


def test_electricity_bill_in_units_is_kwh():
    r = calculate("12500", "units", GRID_IN)
    assert r.kg_co2e == Decimal("8437.500000")
    assert r.t_co2e == Decimal("8.437500")


def test_mwh_converts_to_kwh_exactly():
    assert calculate("12.5", "MWh", GRID_IN).kg_co2e == Decimal("8437.500000")


def test_litres_spellings_agree():
    a = calculate("200", "Ltr", DIESEL).kg_co2e
    b = calculate("0.2", "kL", DIESEL).kg_co2e
    assert a == b == Decimal("514.164000")


def test_tonne_km_unit():
    # 3 tonnes moved 150 km = 450 tonne.km
    assert calculate("450", "tkm", FREIGHT).kg_co2e == Decimal("45.000000")


def test_mt_means_metric_tonne_not_megatonne():
    steel_mass = Factor("x", "x", "x", 3, "steel", "tonnes", Decimal("1850"))
    assert calculate("2", "MT", steel_mass).t_co2e == Decimal("3.700000")


def test_dimension_mismatch_is_rejected():
    with pytest.raises(UnitMismatch):
        calculate("100", "litres", GRID_IN)


def test_spend_needs_explicit_exchange_rate():
    with pytest.raises(MissingExchangeRate):
        calculate("100000", "INR", STEEL_SPEND)


def test_spend_with_exchange_rate():
    r = calculate("100000", "INR", STEEL_SPEND, exchange_rate="0.0120")
    assert r.kg_co2e == Decimal("1440.000000")
    assert r.trace["exchange_rate"] == "0.0120"


def test_same_currency_needs_no_rate():
    assert calculate("500", "USD", STEEL_SPEND).kg_co2e == Decimal("600.000000")


def test_currency_against_physical_unit_is_rejected():
    with pytest.raises(UnitMismatch):
        calculate("500", "USD", GRID_IN)


def test_negative_quantity_rejected():
    with pytest.raises(ValueError):
        calculate("-1", "kWh", GRID_IN)


def test_unknown_unit_rejected():
    with pytest.raises(UnknownUnit):
        calculate("5", "bananas", GRID_IN)


def test_trace_has_everything_needed_to_replay():
    r = calculate("100", "kWh", GRID_IN)
    t = r.trace
    assert t["factor_id"] == GRID_IN.factor_id
    assert t["factor_version"] == "v22.0"
    assert t["quantity_in_factor_unit"] == "100"
    assert Decimal(t["quantity_in_factor_unit"]) * Decimal(t["kgco2e_per_unit"]) == r.kg_co2e
