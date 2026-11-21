import "server-only";

export type Flag = { code: string; message: string; line_index: number | null };

export type LineItem = {
  description: string;
  quantity: string | null;
  unit: string | null;
  amount: string | null;
  category: string;
  is_activity: boolean;
  page: number;
  box_2d: [number, number, number, number] | null;
  confidence: number;
};

export type ExtractedDocument = {
  doc_type: string;
  supplier: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  period_start: string | null;
  period_end: string | null;
  currency: string | null;
  country: string | null;
  line_items: LineItem[];
};

export type DocSummary = {
  id: string;
  filename: string;
  status: "processing" | "done" | "failed";
  uploaded_at: string;
  needs_review: boolean;
  flags: Flag[];
  model: string | null;
  error: string | null;
  document: ExtractedDocument | null;
};

export type LineResult = {
  line_index: number;
  description: string;
  scope: 1 | 2 | 3 | null;
  factor_id: string | null;
  factor_name: string | null;
  method: string;
  kg_co2e: string | null;
  trace: Record<string, string | null> | null;
};

export type AuditEvent = { at: string; event: string; detail_json: string | null };

export type DocDetail = DocSummary & { lines: LineResult[]; audit: AuditEvent[] };

export type Summary = {
  total_t: number;
  by_scope_t: Record<"1" | "2" | "3", number>;
  monthly: { month: string; s1: number; s2: number; s3: number }[];
  top_sources: { name: string; site: string; scope: 1 | 2 | 3; tonnes: number }[];
  review_count: number;
  documents: number;
};

const base = () => (process.env.CARBONTRACE_API_URL ?? "").replace(/\/$/, "");

// Server only: the key never reaches the browser.
export function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${base()}${path}`, {
    ...init,
    cache: "no-store",
    headers: { ...init.headers, "x-api-key": process.env.CARBONTRACE_API_KEY ?? "" },
  });
}

async function getJson<T>(path: string): Promise<T | null> {
  if (!base()) return null;
  try {
    const res = await apiFetch(path);
    return res.ok ? ((await res.json()) as T) : null;
  } catch {
    return null;
  }
}

export const getSummary = () => getJson<Summary>("/summary");
export const getDocuments = () => getJson<DocSummary[]>("/documents");
export const getDocument = (id: string) => getJson<DocDetail>(`/documents/${encodeURIComponent(id)}`);
