"""Extract line items from a bill or invoice with Gemini structured output.

The model only reads the document. It returns quantities, units, categories and bounding boxes;
validation and arithmetic happen elsewhere. If a model hits its free-tier quota or fails, the next
model in MODEL_CHAIN is tried.

Run: python -m carbontrace.extract path/to/invoice.pdf
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from carbontrace.schema import ExtractedDocument, Flag
from carbontrace.validate import check

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Tried in order; override with GEMINI_MODELS="model-a,model-b" when Google retires a model.
DEFAULT_MODELS = "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash,gemini-3.1-flash-lite"
MODEL_CHAIN = [m.strip() for m in os.environ.get("GEMINI_MODELS", DEFAULT_MODELS).split(",") if m.strip()]

PROMPT = """You read business documents for carbon accounting: electricity bills, fuel receipts,
freight invoices and supplier invoices. Extract every line that represents a physical activity or a
purchase. Rules:
- Copy quantities and units exactly as printed. Do not convert units and do not do any arithmetic.
- Use digits only for numbers, without thousands separators.
- For electricity bills, the consumption line (units or kWh consumed) is the key line item.
- Mark is_activity false for charges, taxes, duties, demand (kVA) charges and surcharges such as a
  fuel adjustment charge that reuse another line's consumption; counting them would double-count.
- For freight, capture origin, destination, weight and distance when printed.
- Give each line a bounding box [ymin, xmin, ymax, xmax] scaled 0-1000 on its page.
- Set confidence below 0.7 when text is blurred, cut off, or ambiguous.
- Dates as YYYY-MM-DD. Currency as an ISO 4217 code. Country as an ISO 3166 alpha-2 code.
- If a field is not printed, leave it null. Never guess a value."""


class ExtractionError(RuntimeError):
    pass


@dataclass
class Extraction:
    document: ExtractedDocument
    flags: list[Flag]
    model: str
    attempts: list[dict] = field(default_factory=list)

    @property
    def needs_review(self) -> bool:
        return bool(self.flags)


def _client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ExtractionError("GEMINI_API_KEY is not set. Add it to api/.env or your environment.")
    return genai.Client(api_key=key)


def extract(data: bytes, mime_type: str, *, client: genai.Client | None = None) -> Extraction:
    client = client or _client()
    attempts: list[dict] = []
    for model in MODEL_CHAIN:
        started = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=model,
                contents=[types.Part.from_bytes(data=data, mime_type=mime_type), PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedDocument,
                    temperature=0,
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                    http_options=types.HttpOptions(timeout=90_000),
                ),
            )
        except errors.ClientError as exc:
            attempts.append({"model": model, "ok": False, "error": f"ClientError {exc.code}"})
            # 404 (retired model) and 429 (quota) are model-specific; any other 4xx means the request is wrong.
            if exc.code not in (404, 429):
                raise ExtractionError(str(exc)) from exc
            continue
        except Exception as exc:  # 5xx, timeouts and connection drops: try the next model
            attempts.append({"model": model, "ok": False, "error": type(exc).__name__})
            continue
        doc = response.parsed
        if not isinstance(doc, ExtractedDocument):
            doc = ExtractedDocument.model_validate_json(response.text)
        attempts.append({"model": model, "ok": True, "seconds": round(time.perf_counter() - started, 2)})
        return Extraction(document=doc, flags=check(doc), model=model, attempts=attempts)
    raise ExtractionError(f"All models failed: {attempts}")


def extract_file(path: str | Path, **kwargs) -> Extraction:
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or "application/pdf"
    return extract(path.read_bytes(), mime, **kwargs)


if __name__ == "__main__":
    result = extract_file(sys.argv[1])
    print(json.dumps({
        "model": result.model,
        "attempts": result.attempts,
        "needs_review": result.needs_review,
        "flags": [f.model_dump() for f in result.flags],
        "document": result.document.model_dump(mode="json"),
    }, indent=2, ensure_ascii=False))
