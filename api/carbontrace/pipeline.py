"""Extract -> match -> calculate for one document."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from carbontrace.calc import Factor, MissingExchangeRate, UnitMismatch, calculate
from carbontrace.extract import Extraction, extract
from carbontrace.match import Picker, gemini_picker, match_document
from carbontrace.schema import ExtractedDocument, Flag, LineItem
from carbontrace.units import UnknownUnit, parse_unit, try_parse_unit, ureg


@dataclass
class LineResult:
    line_index: int
    description: str
    scope: int | None
    factor_id: str | None
    factor_name: str | None
    method: str
    kg_co2e: Decimal | None
    trace: dict | None = None


@dataclass
class PipelineResult:
    document: ExtractedDocument
    flags: list[Flag]
    lines: list[LineResult]
    model: str = ""
    attempts: list[dict] = field(default_factory=list)

    @property
    def needs_review(self) -> bool:
        return bool(self.flags)

    @property
    def kg_by_scope(self) -> dict[int, Decimal]:
        totals: dict[int, Decimal] = {}
        for line in self.lines:
            if line.kg_co2e is not None and line.scope:
                totals[line.scope] = totals.get(line.scope, Decimal(0)) + line.kg_co2e
        return totals


def activity_amount(item: LineItem, factor: Factor) -> tuple[str, str, str | None]:
    """Quantity and unit to feed the engine. Freight printed as weight plus distance becomes tonne-km here,
    in code, so the model never multiplies."""
    factor_unit = parse_unit(factor.unit)
    tkm = ureg.parse_units("metric_ton * kilometer")
    item_unit = try_parse_unit(item.unit) if item.unit else None
    if (
        factor_unit.dimensionality == tkm.dimensionality
        and item_unit is not None
        and item_unit.dimensionality == ureg.metric_ton.dimensionality
        and item.distance_km
    ):
        tonnes = Decimal(str((Decimal(item.quantity.replace(",", "")) * item_unit).to(ureg.metric_ton).magnitude))
        km = Decimal(item.distance_km.replace(",", ""))
        return str(tonnes * km), "tkm", f"{tonnes} t x {km} km"
    return (item.quantity or "").replace(",", ""), item.unit or "", None


def run(extraction: Extraction, picker: Picker = gemini_picker) -> PipelineResult:
    doc = extraction.document
    flags = list(extraction.flags)
    matches, match_flags = match_document(doc, picker)
    flags += match_flags
    lines: list[LineResult] = []
    for m in matches:
        item = doc.line_items[m.line_index]
        kg, trace = None, None
        if m.factor is not None:
            try:
                qty, unit, note = activity_amount(item, m.factor)
                result = calculate(qty, unit, m.factor)
                kg, trace = result.kg_co2e, {**result.trace, "derived_quantity": note, "match_method": m.method, "match_reason": m.reason}
            except MissingExchangeRate:
                flags.append(Flag(code="needs_exchange_rate", message="Spend is in a different currency from the factor. Add an exchange rate.", line_index=m.line_index))
            except (UnitMismatch, UnknownUnit, InvalidOperation, ValueError, AttributeError) as exc:
                flags.append(Flag(code="calc_failed", message=f"Couldn't calculate: {exc}", line_index=m.line_index))
        lines.append(LineResult(
            line_index=m.line_index,
            description=item.description,
            scope=m.factor.scope if m.factor else None,
            factor_id=m.factor.factor_id if m.factor else None,
            factor_name=m.factor.name if m.factor else None,
            method=m.method,
            kg_co2e=kg,
            trace=trace,
        ))
    return PipelineResult(doc, flags, lines, extraction.model, extraction.attempts)


def process(data: bytes, mime_type: str) -> PipelineResult:
    return run(extract(data, mime_type))
