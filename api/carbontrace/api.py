"""HTTP API. Run: uvicorn carbontrace.api:app --reload"""

from __future__ import annotations

import hashlib
import os
import secrets
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from carbontrace import pipeline, store

DATA = Path(__file__).resolve().parents[1] / "data"
UPLOADS = Path(os.environ.get("CARBONTRACE_UPLOADS", DATA / "uploads"))
DB_PATH = os.environ.get("CARBONTRACE_DB", str(DATA / "carbontrace.db"))
MAX_BYTES = 15 * 1024 * 1024
# Checked against the file's first bytes, not just the client's claimed type.
SIGNATURES = {
    "application/pdf": (b"%PDF",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/webp": (b"RIFF",),
}

app = FastAPI(title="CarbonTrace API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3100").split(",")],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

UPLOADS.mkdir(parents=True, exist_ok=True)
conn = store.connect(DB_PATH)
# Serverless: the database lives in /tmp and starts empty, so refill it from the committed benchmark outputs.
if os.environ.get("CARBONTRACE_SEED_DEMO") == "1" and not store.list_documents(conn):
    from carbontrace.demo import seed

    seed(conn)
# Serverless platforms may freeze background work after the response, so process inside the request there.
SYNC = os.environ.get("CARBONTRACE_SYNC") == "1"

API_KEY = os.environ.get("CARBONTRACE_API_KEY", "")
DEV_NO_AUTH = os.environ.get("CARBONTRACE_DEV") == "1"
if not API_KEY and not DEV_NO_AUTH:
    raise RuntimeError("Set CARBONTRACE_API_KEY, or CARBONTRACE_DEV=1 for local development without auth.")


def require_key(x_api_key: str = Header("")) -> None:
    """Every route except /health needs the shared key. The web app sends it server-side, never from the browser."""
    if DEV_NO_AUTH and not API_KEY:
        return
    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(401, "Missing or wrong API key.")


auth = [Depends(require_key)]


def process_file(doc_id: str, path: Path, mime: str) -> None:
    try:
        result = pipeline.process(path.read_bytes(), mime)
        store.save_result(conn, doc_id, result)
    except Exception as exc:  # keep the document visible as failed instead of stuck in processing
        store.fail(conn, doc_id, f"{type(exc).__name__}: {exc}")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/documents", status_code=202, dependencies=auth)
async def upload(file: UploadFile, background: BackgroundTasks) -> dict:
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File is larger than 15 MB.")
    if not data:
        raise HTTPException(400, "File is empty.")
    mime = file.content_type or ""
    if mime not in SIGNATURES or not data.startswith(SIGNATURES[mime]):
        raise HTTPException(415, "Upload a PDF, PNG, JPEG or WebP file.")
    sha = hashlib.sha256(data).hexdigest()
    existing = store.find_by_hash(conn, sha)
    if existing:
        return {"id": existing, "duplicate": True}
    suffix = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}[mime]
    path = UPLOADS / f"{sha[:16]}{suffix}"
    path.write_bytes(data)
    name = Path(file.filename or "upload").name[:200]
    doc_id = store.create_document(conn, name, mime, sha, str(path))
    if SYNC:
        process_file(doc_id, path, mime)
    else:
        background.add_task(process_file, doc_id, path, mime)
    return {"id": doc_id, "duplicate": False}


@app.get("/documents", dependencies=auth)
def documents() -> list[dict]:
    return store.list_documents(conn)


@app.get("/documents/{doc_id}", dependencies=auth)
def document(doc_id: str) -> dict:
    doc = store.get_document(conn, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found.")
    return doc


@app.get("/documents/{doc_id}/file", dependencies=auth)
def document_file(doc_id: str) -> FileResponse:
    row = conn.execute("SELECT path, mime FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Document not found.")
    path = Path(row["path"])
    if not path.is_absolute():  # seeded demo documents are stored relative to api/
        path = DATA.parent / path
    return FileResponse(path, media_type=row["mime"])


class Review(BaseModel):
    note: str = ""


@app.post("/documents/{doc_id}/review", dependencies=auth)
def review(doc_id: str, body: Review) -> dict:
    if not store.mark_reviewed(conn, doc_id, body.note[:500]):
        raise HTTPException(409, "Only processed documents can be marked reviewed.")
    return {"ok": True}


@app.get("/summary", dependencies=auth)
def summary() -> dict:
    return store.summary(conn)
