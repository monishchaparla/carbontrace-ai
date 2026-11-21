# CarbonTrace AI

Audit-ready Scope 1, 2 and 3 carbon accounting from messy bills, invoices and manifests.

Upload a document, and CarbonTrace extracts each line item, maps it to an emission factor, and
calculates tCO2e with deterministic Python math, keeping a trace back to the exact line on the
source document.

> Status: in active development. The dashboard currently runs on sample data.

## Planned architecture

| Layer | Choice |
|---|---|
| Extraction | Gemini (vision + structured JSON output), with validation and a human-review queue |
| Emission factors | EPA Supply Chain GHG factors, UK DESNZ conversion factors, India CEA grid factor |
| Retrieval | Postgres full-text + pgvector embeddings + cross-encoder reranking |
| Calculation | Deterministic Python engine with unit validation (the LLM never does arithmetic) |
| Backend | FastAPI, PostgreSQL with an append-only audit log |
| Frontend | Next.js, Tailwind CSS, Recharts |
| Evals | Synthetic invoice benchmark: extraction accuracy, Recall@3, calculation error |

## Repository layout

```
api/        Python engine: emission factors, calculation, tests
web/        Next.js frontend
DESIGN.md   Design system (colours, type, layout, components)
```

## Run the frontend

```bash
cd web
npm install
npm run dev
```

## Design

See [DESIGN.md](DESIGN.md). Light and dark themes follow the system setting by default.
