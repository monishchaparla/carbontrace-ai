"""SQLite storage with an append-only audit log.

shortcut: SQLite on local disk, fine for one instance; move to Postgres when deploying more than one API instance.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  mime TEXT NOT NULL,
  sha256 TEXT NOT NULL UNIQUE,
  path TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('processing', 'done', 'failed')),
  uploaded_at TEXT NOT NULL,
  doc_json TEXT,
  flags_json TEXT,
  needs_review INTEGER NOT NULL DEFAULT 0,
  model TEXT,
  error TEXT
);
CREATE TABLE IF NOT EXISTS line_results (
  document_id TEXT NOT NULL REFERENCES documents(id),
  line_index INTEGER NOT NULL,
  description TEXT,
  scope INTEGER,
  factor_id TEXT,
  factor_name TEXT,
  method TEXT,
  kg_co2e TEXT,
  trace_json TEXT,
  PRIMARY KEY (document_id, line_index)
);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  document_id TEXT,
  event TEXT NOT NULL,
  detail_json TEXT
);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def audit(conn: sqlite3.Connection, document_id: str | None, event: str, detail: dict | None = None) -> None:
    conn.execute(
        "INSERT INTO audit_log (at, document_id, event, detail_json) VALUES (?, ?, ?, ?)",
        (now(), document_id, event, json.dumps(detail or {}, default=str)),
    )


def find_by_hash(conn: sqlite3.Connection, sha256: str) -> str | None:
    row = conn.execute("SELECT id FROM documents WHERE sha256 = ?", (sha256,)).fetchone()
    return row["id"] if row else None


def create_document(conn: sqlite3.Connection, filename: str, mime: str, sha256: str, path: str) -> str:
    doc_id = uuid.uuid4().hex[:12]
    with conn:
        conn.execute(
            "INSERT INTO documents (id, filename, mime, sha256, path, status, uploaded_at) VALUES (?, ?, ?, ?, ?, 'processing', ?)",
            (doc_id, filename, mime, sha256, path, now()),
        )
        audit(conn, doc_id, "uploaded", {"filename": filename, "sha256": sha256})
    return doc_id


def save_result(conn: sqlite3.Connection, doc_id: str, result) -> None:
    with conn:
        conn.execute(
            "UPDATE documents SET status='done', doc_json=?, flags_json=?, needs_review=?, model=? WHERE id=?",
            (
                result.document.model_dump_json(),
                json.dumps([f.model_dump() for f in result.flags]),
                int(result.needs_review),
                result.model,
                doc_id,
            ),
        )
        for line in result.lines:
            conn.execute(
                "INSERT OR REPLACE INTO line_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    doc_id, line.line_index, line.description, line.scope, line.factor_id, line.factor_name, line.method,
                    str(line.kg_co2e) if line.kg_co2e is not None else None,
                    json.dumps(line.trace) if line.trace else None,
                ),
            )
        audit(conn, doc_id, "processed", {
            "model": result.model,
            "attempts": result.attempts,
            "flags": [f.code for f in result.flags],
            "kg_by_scope": {str(k): str(v) for k, v in result.kg_by_scope.items()},
        })


def fail(conn: sqlite3.Connection, doc_id: str, error: str) -> None:
    with conn:
        conn.execute("UPDATE documents SET status='failed', error=? WHERE id=?", (error[:500], doc_id))
        audit(conn, doc_id, "failed", {"error": error[:500]})


def mark_reviewed(conn: sqlite3.Connection, doc_id: str, note: str) -> bool:
    with conn:
        changed = conn.execute("UPDATE documents SET needs_review=0 WHERE id=? AND status='done'", (doc_id,)).rowcount
        if changed:
            audit(conn, doc_id, "reviewed", {"note": note})
    return bool(changed)


def _doc_row(row: sqlite3.Row, lines: list[sqlite3.Row] | None = None) -> dict:
    doc = json.loads(row["doc_json"]) if row["doc_json"] else None
    out = {
        "id": row["id"],
        "filename": row["filename"],
        "status": row["status"],
        "uploaded_at": row["uploaded_at"],
        "needs_review": bool(row["needs_review"]),
        "flags": json.loads(row["flags_json"]) if row["flags_json"] else [],
        "model": row["model"],
        "error": row["error"],
        "document": doc,
    }
    if lines is not None:
        out["lines"] = [
            {
                "line_index": l["line_index"], "description": l["description"], "scope": l["scope"],
                "factor_id": l["factor_id"], "factor_name": l["factor_name"], "method": l["method"],
                "kg_co2e": l["kg_co2e"], "trace": json.loads(l["trace_json"]) if l["trace_json"] else None,
            }
            for l in lines
        ]
    return out


def list_documents(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
    return [_doc_row(r) for r in rows]


def get_document(conn: sqlite3.Connection, doc_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if row is None:
        return None
    lines = conn.execute("SELECT * FROM line_results WHERE document_id = ? ORDER BY line_index", (doc_id,)).fetchall()
    out = _doc_row(row, lines)
    out["audit"] = [dict(r) for r in conn.execute("SELECT at, event, detail_json FROM audit_log WHERE document_id = ? ORDER BY id", (doc_id,))]
    return out


def summary(conn: sqlite3.Connection) -> dict:
    """Totals in tonnes for the dashboard. Month comes from the period end, else the invoice date, else upload date."""
    rows = conn.execute(
        "SELECT d.id, d.filename, d.uploaded_at, d.doc_json, l.scope, l.factor_name, l.kg_co2e "
        "FROM line_results l JOIN documents d ON d.id = l.document_id WHERE d.status='done' AND l.kg_co2e IS NOT NULL"
    ).fetchall()
    by_scope = {1: Decimal(0), 2: Decimal(0), 3: Decimal(0)}
    monthly: dict[str, dict[int, Decimal]] = {}
    sources: dict[tuple[str, str, int], Decimal] = {}
    for r in rows:
        kg = Decimal(r["kg_co2e"])
        scope = r["scope"]
        doc = json.loads(r["doc_json"]) if r["doc_json"] else {}
        month = (doc.get("period_end") or doc.get("invoice_date") or r["uploaded_at"])[:7]
        by_scope[scope] += kg
        monthly.setdefault(month, {1: Decimal(0), 2: Decimal(0), 3: Decimal(0)})[scope] += kg
        key = (r["factor_name"], doc.get("supplier") or r["filename"], scope)
        sources[key] = sources.get(key, Decimal(0)) + kg

    def t(kg: Decimal) -> float:
        return round(float(kg / 1000), 3)

    review = conn.execute("SELECT COUNT(*) FROM documents WHERE needs_review=1 AND status='done'").fetchone()[0]
    return {
        "total_t": t(sum(by_scope.values())),
        "by_scope_t": {str(k): t(v) for k, v in by_scope.items()},
        "monthly": [{"month": m, "s1": t(v[1]), "s2": t(v[2]), "s3": t(v[3])} for m, v in sorted(monthly.items())],
        "top_sources": [
            {"name": name, "site": site, "scope": scope, "tonnes": t(kg)}
            for (name, site, scope), kg in sorted(sources.items(), key=lambda kv: kv[1], reverse=True)[:5]
        ],
        "review_count": review,
        "documents": conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
    }
