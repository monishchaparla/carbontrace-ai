from decimal import Decimal

from carbontrace.extract import Extraction
from carbontrace.match import Pick, candidates
from carbontrace.pipeline import run
from carbontrace.schema import Category, DocType, ExtractedDocument, LineItem
from carbontrace.validate import check


def li(**kw):
    base = dict(description="x", quantity="1", unit="kWh", category=Category.electricity, is_activity=True, confidence=0.95)
    base.update(kw)
    return LineItem(**base)


def extraction(*items, currency="INR"):
    doc = ExtractedDocument(doc_type=DocType.other, currency=currency, country="IN", line_items=list(items))
    return Extraction(document=doc, flags=check(doc), model="fake")


def pick_first(doc, shortlists):
    return [Pick(line_index=i, factor_id=c.iloc[0]["factor_id"], reason="first") for i, c in shortlists.items()]


def test_india_electricity_bill_end_to_end():
    r = run(extraction(li(description="Energy consumed", quantity="24500", amount="232750")), picker=pick_first)
    assert r.lines[0].kg_co2e == Decimal("16537.500000")  # 24,500 kWh x 0.675
    assert r.kg_by_scope == {2: Decimal("16537.500000")}
    assert r.flags == []


def test_freight_weight_and_distance_become_tonne_km_in_code():
    freight = li(description="Road freight Pune to Mumbai, HGV", quantity="3", unit="MT", distance_km="150",
                 category=Category.freight, fuel_or_material="hgv")
    tkm_factor = candidates(freight.model_copy(update={"unit": "tkm"})).iloc[0]["factor_id"]
    r = run(extraction(freight), picker=lambda d, s: [Pick(line_index=0, factor_id=tkm_factor, reason="x")])
    trace = r.lines[0].trace
    assert trace["factor_unit"] == "tonne.km"
    assert trace["derived_quantity"] == "3 t x 150 km"
    assert trace["input_quantity"] == "450"


def test_charges_produce_no_emissions():
    r = run(extraction(li(is_activity=False), li(description="Energy", quantity="100", amount="950")), picker=pick_first)
    assert [l.line_index for l in r.lines] == [1]
