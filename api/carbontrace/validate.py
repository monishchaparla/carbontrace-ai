"""Deterministic checks that decide whether an extraction needs human review.

Nothing here calls a model. Each check returns a Flag with a plain message an analyst can act on.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from carbontrace.schema import Category, ExtractedDocument, Flag
from carbontrace.units import try_parse_unit, ureg

LOW_CONFIDENCE = 0.7
MAX_PERIOD_DAYS = 400  # a billing or service period longer than ~13 months is suspicious
# Plausible grid tariff band in rupees per kWh; outside it the unit (kWh vs MWh) is probably wrong.
INR_PER_KWH_RANGE = (Decimal("2"), Decimal("25"))


def _num(text: str | None) -> Decimal | None:
    if text is None:
        return None
    try:
        return Decimal(text.replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return None


def _date(text: str | None) -> date | None:
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def check(doc: ExtractedDocument, today: date | None = None) -> list[Flag]:
    today = today or date.today()
    flags: list[Flag] = []

    start, end = _date(doc.period_start), _date(doc.period_end)
    if start and end:
        if end < start:
            flags.append(Flag(code="period_reversed", message="Period ends before it starts."))
        elif (end - start).days > MAX_PERIOD_DAYS:
            months = round((end - start).days / 30.4)
            flags.append(Flag(code="period_too_long", message=f"Date range spans {months} months."))
    issued = _date(doc.invoice_date)
    if issued and issued > today:
        flags.append(Flag(code="future_date", message="Invoice date is in the future."))
    if not doc.line_items:
        flags.append(Flag(code="no_lines", message="No line items were found."))

    activities = [(i, item) for i, item in enumerate(doc.line_items) if item.is_activity]
    if doc.line_items and not activities:
        flags.append(Flag(code="no_activity", message="No consumption or activity line was found."))

    seen: dict[tuple[str, str], int] = {}
    for i, item in activities:
        key = ((item.quantity or "").strip(), (item.unit or "").strip().lower())
        if key[0] and key in seen:
            flags.append(Flag(
                code="possible_double_count",
                message=f"Same quantity as line {seen[key] + 1} ({item.quantity} {item.unit}). Check it isn't counted twice.",
                line_index=i,
            ))
        seen.setdefault(key, i)

    for i, item in activities:
        qty = _num(item.quantity)
        if item.category != Category.other and qty is None:
            flags.append(Flag(code="missing_quantity", message="Quantity is missing or not a number.", line_index=i))
        if qty is not None and qty < 0:
            flags.append(Flag(code="negative_quantity", message="Quantity is negative.", line_index=i))
        unit = try_parse_unit(item.unit) if item.unit else None
        if item.unit and unit is None:
            flags.append(Flag(code="unknown_unit", message=f"Unit {item.unit!r} isn't recognised.", line_index=i))
        if item.confidence < LOW_CONFIDENCE:
            flags.append(Flag(code="low_confidence", message=f"Read with {item.confidence:.0%} confidence.", line_index=i))

        # Electricity: check the implied price per kWh against a plausible tariff band.
        amount = _num(item.amount)
        if (
            item.category == Category.electricity
            and unit is not None
            and qty
            and amount
            and (doc.currency or "").upper() == "INR"
            and unit.dimensionality == ureg.kilowatt_hour.dimensionality
        ):
            kwh = Decimal(str((qty * unit).to(ureg.kilowatt_hour).magnitude))
            if kwh > 0:
                per_kwh = amount / kwh
                low, high = INR_PER_KWH_RANGE
                if not (low <= per_kwh <= high):
                    flags.append(Flag(
                        code="unit_suspect",
                        message=f"Unit reads {item.unit}, but the price works out to ₹{per_kwh:.2f} per kWh. Check kWh vs MWh.",
                        line_index=i,
                    ))
    return flags
