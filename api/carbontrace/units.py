"""Unit handling shared by the factor builder and the calculation engine.

Invoices spell units many ways ("KWH", "units", "Ltr", "MT", "tkm"). Everything is parsed
into a pint quantity on one registry so conversions are exact and dimension mismatches fail
loudly instead of producing a wrong number.
"""

from __future__ import annotations

import re
from decimal import Decimal

import pint

ureg = pint.UnitRegistry(non_int_type=Decimal)
# Dimensions that are not physical but must never be mixed up.
ureg.define("passenger = [passenger]")
ureg.define("USD = [currency_usd]")
ureg.define("GBP = [currency_gbp]")
ureg.define("INR = [currency_inr]")
ureg.define("EUR = [currency_eur]")
ureg.define("room_night = [room_night]")

# Lower-cased invoice spellings -> pint expressions.
_ALIASES: dict[str, str] = {
    "kwh": "kilowatt_hour",
    "kwh (net cv)": "kilowatt_hour",
    "kwh (gross cv)": "kilowatt_hour",
    "units": "kilowatt_hour",  # Indian electricity bills bill "units" = kWh
    "unit (kwh)": "kilowatt_hour",
    "mwh": "megawatt_hour",
    "gj": "gigajoule",
    "mj": "megajoule",
    "therms": "therm",
    "room per night": "room_night",
    "room nights": "room_night",
    "gwh": "gigawatt_hour",
    "l": "liter",
    "ltr": "liter",
    "ltrs": "liter",
    "litre": "liter",
    "litres": "liter",
    "liters": "liter",
    "kl": "kiloliter",
    "million litres": "megaliter",
    "m3": "meter**3",
    "cubic metres": "meter**3",
    "scm": "meter**3",  # standard cubic metre (gas)
    "kg": "kilogram",
    "kgs": "kilogram",
    "t": "metric_ton",
    "mt": "metric_ton",  # Indian invoices: MT = metric tonne, never megatonne
    "tonne": "metric_ton",
    "tonnes": "metric_ton",
    "ton": "metric_ton",
    "km": "kilometer",
    "kms": "kilometer",
    "miles": "mile",
    "tonne.km": "metric_ton * kilometer",
    "tonne km": "metric_ton * kilometer",
    "tkm": "metric_ton * kilometer",
    "passenger.km": "passenger * kilometer",
    "pkm": "passenger * kilometer",
    "usd": "USD",
    "gbp": "GBP",
    "inr": "INR",
    "rs": "INR",
    "rs.": "INR",
    "eur": "EUR",
}


class UnknownUnit(ValueError):
    """The unit text could not be mapped to a known unit."""


def parse_unit(text: str) -> pint.Unit:
    """Map an invoice or dataset unit string to a pint unit, or raise UnknownUnit."""
    key = re.sub(r"\s+", " ", text.strip().lower())
    expr = _ALIASES.get(key, key)
    try:
        return ureg.parse_units(expr)
    except (pint.UndefinedUnitError, pint.DefinitionSyntaxError, ValueError, AttributeError) as exc:
        raise UnknownUnit(f"Unknown unit: {text!r}") from exc


def try_parse_unit(text: str) -> pint.Unit | None:
    try:
        return parse_unit(text)
    except UnknownUnit:
        return None
