from datetime import date

from carbontrace.schema import Category, DocType, ExtractedDocument, LineItem
from carbontrace.validate import check

TODAY = date(2026, 11, 21)


def doc(**kw):
    base = dict(doc_type=DocType.electricity_bill, currency="INR", period_start="2026-09-01", period_end="2026-09-30", line_items=[])
    base.update(kw)
    return ExtractedDocument(**base)


def line(**kw):
    base = dict(description="Energy consumed", quantity="24500", unit="kWh", amount="232750", category=Category.electricity, is_activity=True, confidence=0.95)
    base.update(kw)
    return LineItem(**base)


def codes(flags):
    return {f.code for f in flags}


def test_clean_bill_has_no_flags():
    assert check(doc(line_items=[line()]), TODAY) == []


def test_mwh_misprint_is_flagged_by_price_per_kwh():
    assert "unit_suspect" in codes(check(doc(line_items=[line(unit="MWh")]), TODAY))


def test_long_period_flagged():
    assert "period_too_long" in codes(check(doc(period_end="2027-11-01", line_items=[line()]), TODAY))


def test_reversed_period_flagged():
    assert "period_reversed" in codes(check(doc(period_start="2026-10-01", period_end="2026-09-01", line_items=[line()]), TODAY))


def test_low_confidence_flagged():
    assert "low_confidence" in codes(check(doc(line_items=[line(confidence=0.4)]), TODAY))


def test_unknown_unit_flagged():
    assert "unknown_unit" in codes(check(doc(line_items=[line(unit="bananas")]), TODAY))


def test_missing_quantity_flagged():
    assert "missing_quantity" in codes(check(doc(line_items=[line(quantity=None)]), TODAY))


def test_future_invoice_date_flagged():
    assert "future_date" in codes(check(doc(invoice_date="2027-01-01", line_items=[line()]), TODAY))


def test_no_lines_flagged():
    assert "no_lines" in codes(check(doc(), TODAY))


def test_charges_are_not_checked_as_activities():
    charges = [line(description="Demand charge", quantity="120", unit="kVA", amount="52800", is_activity=False),
               line(description="Electricity duty", quantity=None, unit=None, amount="17456", is_activity=False)]
    assert check(doc(line_items=[line(), *charges]), TODAY) == []


def test_repeated_activity_quantity_flagged_as_double_count():
    surcharge_marked_as_activity = line(description="Fuel adjustment charge", amount="8330")
    assert "possible_double_count" in codes(check(doc(line_items=[line(), surcharge_marked_as_activity]), TODAY))


def test_only_charges_means_no_activity():
    assert "no_activity" in codes(check(doc(line_items=[line(is_activity=False)]), TODAY))


def test_indian_units_spelling_is_fine():
    assert check(doc(line_items=[line(unit="units")]), TODAY) == []
