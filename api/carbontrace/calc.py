"""Deterministic emissions calculation.

The language model only extracts quantity, unit and category. All arithmetic happens here:
emissions = activity quantity (converted to the factor's unit) x emission factor.
Every result carries a trace so an auditor can replay the calculation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

import pint

from carbontrace.units import parse_unit, ureg

_SIX = Decimal("0.000001")


class UnitMismatch(ValueError):
    """The activity unit cannot be converted to the factor's unit."""


class MissingExchangeRate(ValueError):
    """A spend-based factor needs an explicit exchange rate for the invoice currency."""


@dataclass(frozen=True)
class Factor:
    factor_id: str
    source: str
    source_version: str
    scope: int
    name: str
    unit: str  # unit of the denominator, e.g. "kWh", "litres", "USD"
    kgco2e_per_unit: Decimal


@dataclass(frozen=True)
class Result:
    kg_co2e: Decimal
    t_co2e: Decimal
    trace: dict = field(default_factory=dict)


def _is_currency(unit: pint.Unit) -> bool:
    return any(str(dim).startswith("[currency_") for dim in unit.dimensionality)


def calculate(
    quantity: Decimal | str | int,
    unit: str,
    factor: Factor,
    *,
    exchange_rate: Decimal | str | None = None,
) -> Result:
    """Return emissions for one activity line.

    exchange_rate converts one unit of the invoice currency into the factor's currency
    (for example INR -> USD). It is required when the two currencies differ, and must come
    from a documented source, never from a model.
    """
    qty = Decimal(str(quantity))
    if qty < 0:
        raise ValueError("Quantity cannot be negative")
    if factor.kgco2e_per_unit < 0:
        raise ValueError("Emission factor cannot be negative")

    activity_unit = parse_unit(unit)
    factor_unit = parse_unit(factor.unit)
    rate_used: Decimal | None = None

    if _is_currency(activity_unit) or _is_currency(factor_unit):
        if not (_is_currency(activity_unit) and _is_currency(factor_unit)):
            raise UnitMismatch(f"Cannot convert {unit} to {factor.unit}")
        if activity_unit == factor_unit:
            converted = qty
        elif exchange_rate is None:
            raise MissingExchangeRate(f"Exchange rate needed to convert {unit} to {factor.unit}")
        else:
            rate_used = Decimal(str(exchange_rate))
            if rate_used <= 0:
                raise ValueError("Exchange rate must be positive")
            converted = qty * rate_used
    else:
        try:
            converted = (qty * activity_unit).to(factor_unit).magnitude
        except pint.DimensionalityError as exc:
            raise UnitMismatch(f"Cannot convert {unit} to {factor.unit}") from exc
        converted = Decimal(str(converted))

    kg = (converted * factor.kgco2e_per_unit).quantize(_SIX, rounding=ROUND_HALF_UP)
    tonnes = (kg / Decimal(1000)).quantize(_SIX, rounding=ROUND_HALF_UP)

    trace = {
        "formula": "emissions_kg = quantity_in_factor_unit * kgco2e_per_unit",
        "input_quantity": str(qty),
        "input_unit": unit,
        "factor_id": factor.factor_id,
        "factor_source": factor.source,
        "factor_version": factor.source_version,
        "factor_unit": factor.unit,
        "kgco2e_per_unit": str(factor.kgco2e_per_unit),
        "quantity_in_factor_unit": str(converted),
        "exchange_rate": str(rate_used) if rate_used is not None else None,
        "scope": factor.scope,
    }
    return Result(kg_co2e=kg, t_co2e=tonnes, trace=trace)


def to_unit_string(unit: str) -> str:
    """Canonical pint spelling of a unit, for storing alongside factors."""
    return f"{ureg.Unit(parse_unit(unit)):~}"
