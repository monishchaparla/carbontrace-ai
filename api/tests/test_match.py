from carbontrace.match import INDIA_GRID, Pick, candidates, match_document
from carbontrace.schema import Category, DocType, ExtractedDocument, LineItem
from carbontrace.units import parse_unit


def item(**kw):
    base = dict(description="Energy consumed", quantity="24500", unit="kWh", category=Category.electricity, is_activity=True, confidence=0.95)
    base.update(kw)
    return LineItem(**base)


def doc(*items, country="IN"):
    return ExtractedDocument(doc_type=DocType.other, currency="INR", country=country, line_items=list(items))


def no_model(doc, shortlists):
    raise AssertionError("model should not be called")


DIESEL = dict(description="High speed diesel", unit="litres", category=Category.fuel, fuel_or_material="diesel")


def test_india_electricity_uses_cea_rule_without_model():
    matches, flags = match_document(doc(item()), picker=no_model)
    assert matches[0].factor.factor_id == INDIA_GRID and matches[0].method == "rule" and flags == []


def test_charges_are_not_matched():
    matches, _ = match_document(doc(item(is_activity=False)), picker=no_model)
    assert matches == []


def test_candidates_share_the_line_unit_dimension():
    cands = candidates(item(**{**DIESEL, "unit": "Ltr"}))
    assert not cands.empty
    assert all(parse_unit(u).dimensionality == parse_unit("litre").dimensionality for u in cands["unit"])


def test_keyword_ranking_finds_diesel_in_top_3():
    assert any("diesel" in n.lower() for n in candidates(item(**DIESEL)).head(3)["name"])


def test_road_freight_only_offers_hgv_factors():
    road = item(description="Road freight Pune to Mumbai", quantity="450", unit="tkm", category=Category.freight)
    names = list(candidates(road)["name"])
    assert names and all("hgv" in n.lower() for n in names)


def test_rail_freight_offers_rail_factors():
    rail = item(description="Container by rail, Nagpur to JNPT", quantity="900", unit="tkm", category=Category.freight)
    assert all(n.lower().startswith("rail") for n in candidates(rail)["name"])


def test_model_pick_outside_shortlist_falls_back_and_flags():
    matches, flags = match_document(doc(item(**DIESEL)), picker=lambda d, s: [Pick(line_index=0, factor_id="made-up-id", reason="x")])
    assert matches[0].method == "keyword_fallback"
    assert {f.code for f in flags} == {"factor_uncertain"}


def test_valid_model_pick_is_used():
    chosen = candidates(item(**DIESEL)).iloc[1]["factor_id"]
    matches, flags = match_document(doc(item(**DIESEL)), picker=lambda d, s: [Pick(line_index=0, factor_id=chosen, reason="fits")])
    assert matches[0].factor.factor_id == chosen and matches[0].method == "model" and flags == []
