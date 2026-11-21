import importlib
import sqlite3
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from carbontrace.pipeline import LineResult, PipelineResult
from carbontrace.schema import DocType, ExtractedDocument

PDF = b"%PDF-1.4 fake test file"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CARBONTRACE_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("CARBONTRACE_UPLOADS", str(tmp_path / "up"))
    monkeypatch.setenv("CARBONTRACE_API_KEY", "test-key")
    monkeypatch.delenv("CARBONTRACE_DEV", raising=False)
    import carbontrace.api as api
    api = importlib.reload(api)

    def fake_process(data, mime):
        doc = ExtractedDocument(doc_type=DocType.electricity_bill, supplier="Test Power", period_end="2026-09-30", currency="INR", country="IN", line_items=[])
        lines = [LineResult(0, "Energy", 2, "cea-v22:india-grid-fy2025-26", "India grid", "rule", Decimal("16537.5"), {"formula": "x"})]
        return PipelineResult(doc, [], lines, "fake")

    monkeypatch.setattr(api.pipeline, "process", fake_process)
    return TestClient(api.app, headers={"x-api-key": "test-key"}), api


def test_routes_need_api_key_except_health(client):
    _, api = client
    anon = TestClient(api.app)
    assert anon.get("/health").status_code == 200
    assert anon.get("/documents").status_code == 401
    assert anon.get("/summary", headers={"x-api-key": "wrong"}).status_code == 401
    assert anon.post("/documents", files={"file": ("bill.pdf", PDF, "application/pdf")}).status_code == 401


def test_upload_process_and_summary(client):
    c, _ = client
    r = c.post("/documents", files={"file": ("bill.pdf", PDF, "application/pdf")})
    assert r.status_code == 202
    doc_id = r.json()["id"]
    detail = c.get(f"/documents/{doc_id}").json()
    assert detail["status"] == "done" and detail["lines"][0]["kg_co2e"] == "16537.5"
    assert [a["event"] for a in detail["audit"]] == ["uploaded", "processed"]
    s = c.get("/summary").json()
    assert s["by_scope_t"]["2"] == 16.538 and s["monthly"][0]["month"] == "2026-09"


def test_duplicate_upload_is_not_counted_twice(client):
    c, _ = client
    first = c.post("/documents", files={"file": ("a.pdf", PDF, "application/pdf")}).json()
    second = c.post("/documents", files={"file": ("b.pdf", PDF, "application/pdf")}).json()
    assert second == {"id": first["id"], "duplicate": True}
    assert len(c.get("/documents").json()) == 1


def test_rejects_file_whose_bytes_are_not_a_pdf(client):
    c, _ = client
    r = c.post("/documents", files={"file": ("x.pdf", b"<html>not a pdf", "application/pdf")})
    assert r.status_code == 415


def test_audit_log_is_append_only(client):
    c, api = client
    c.post("/documents", files={"file": ("bill.pdf", PDF, "application/pdf")})
    with pytest.raises(sqlite3.IntegrityError):
        api.conn.execute("DELETE FROM audit_log")
    with pytest.raises(sqlite3.IntegrityError):
        api.conn.execute("UPDATE audit_log SET event='x'")


def test_review_clears_flag_and_is_audited(client):
    c, api = client
    doc_id = c.post("/documents", files={"file": ("bill.pdf", PDF, "application/pdf")}).json()["id"]
    assert c.post(f"/documents/{doc_id}/review", json={"note": "checked"}).status_code == 200
    events = [a["event"] for a in c.get(f"/documents/{doc_id}").json()["audit"]]
    assert events[-1] == "reviewed"
