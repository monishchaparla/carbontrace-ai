"use client";

import { useState, useTransition } from "react";
import type { DocDetail } from "@/lib/api";
import { kgFmt } from "@/lib/format";
import { scopeMeta } from "@/lib/sample-data";
import { markReviewed } from "@/app/documents/[id]/actions";
import { SourcePages, type Highlight } from "@/components/source-pages";

const methodLabel: Record<string, string> = {
  rule: "Matched by rule",
  model: "Picked by model",
  keyword_fallback: "Keyword fallback",
  none: "No match",
};

const eventLabel: Record<string, string> = {
  uploaded: "Uploaded",
  processed: "Processed",
  failed: "Couldn't read",
  reviewed: "Marked reviewed",
};

function detailText(json: string | null): string {
  try {
    const d = JSON.parse(json ?? "{}") as Record<string, unknown>;
    return Object.entries(d)
      .filter(([, v]) => v !== "" && !(Array.isArray(v) && v.length === 0))
      .map(([k, v]) => `${k.replace(/_/g, " ")}: ${typeof v === "object" ? JSON.stringify(v) : String(v)}`)
      .join("; ");
  } catch {
    return "";
  }
}

const when = new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" });

export function AuditView({ doc, fileUrl, mime }: { doc: DocDetail; fileUrl: string; mime: string }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [pending, start] = useTransition();
  const [error, setError] = useState("");
  const items = doc.document?.line_items ?? [];
  const rows = items
    .map((item, i) => ({ item, i, result: doc.lines.find((l) => l.line_index === i) }))
    .sort((a, b) => Number(b.item.is_activity) - Number(a.item.is_activity) || a.i - b.i);

  const sel = selected === null ? null : items[selected];
  const highlight: Highlight = sel?.box_2d ? { page: sel.page, box: sel.box_2d } : null;

  return (
    <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <section aria-label="Source document" className="min-w-0 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:self-start lg:overflow-y-auto">
        <SourcePages src={fileUrl} mime={mime} highlight={highlight} />
      </section>

      <div className="min-w-0 space-y-6">
        {doc.status === "failed" ? (
          <p className="rounded-[10px] bg-fail-wash px-4 py-3 text-sm text-fail">This document could not be read. {doc.error}</p>
        ) : null}

        {doc.flags.length > 0 ? (
          <section aria-labelledby="flags" className="rounded-[10px] border border-rule bg-surface p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <h2 id="flags" className="text-base font-medium">Why this needs review</h2>
              {doc.needs_review ? (
                <button
                  type="button"
                  disabled={pending}
                  onClick={() =>
                    start(async () => {
                      const r = await markReviewed(doc.id);
                      setError(r.ok ? "" : (r.message ?? "Couldn't mark this document reviewed."));
                    })
                  }
                  className="inline-flex h-10 items-center rounded-md bg-pine px-4 text-sm font-medium text-on-pine hover:opacity-90 disabled:opacity-60"
                >
                  {pending ? "Marking reviewed…" : "Mark reviewed"}
                </button>
              ) : null}
            </div>
            <ul className="mt-3 space-y-1.5 text-sm">
              {doc.flags.map((f, i) => (
                <li key={i} className="flex gap-2">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-review-ink" aria-hidden="true" />
                  <span>
                    {f.message}
                    {f.line_index !== null ? <span className="text-ink-2"> (line {f.line_index + 1})</span> : null}
                  </span>
                </li>
              ))}
            </ul>
            <p role="status" className="mt-2 text-sm text-fail">{error}</p>
          </section>
        ) : null}

        <section aria-labelledby="ledger" className="rounded-[10px] border border-rule bg-surface">
          <h2 id="ledger" className="px-5 pt-5 text-base font-medium">Ledger</h2>
          <p className="px-5 pt-1 text-sm text-ink-2">Select a line to see where it came from on the page.</p>
          {rows.length === 0 ? <p className="px-5 py-6 text-sm text-ink-2">No lines were extracted.</p> : null}
          <ul className="mt-3">
            {rows.map(({ item, i, result }) => {
              const active = selected === i;
              const scope = result?.scope ? scopeMeta[result.scope] : null;
              const trace = result?.trace;
              const source = trace?.factor_source ? `${trace.factor_source}${trace.factor_version ? ` ${trace.factor_version}` : ""}` : null;
              return (
                <li key={i} className="border-t border-rule">
                  <button
                    type="button"
                    aria-pressed={active}
                    onClick={() => setSelected(active ? null : i)}
                    className={`block w-full px-5 py-3 text-left transition-colors ${active ? "bg-pine-wash" : "hover:bg-canvas"} ${item.is_activity ? "" : "text-ink-2"}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <div className={`text-sm ${item.is_activity ? "font-medium text-ink" : ""}`}>{item.description}</div>
                        <div className="num text-xs text-ink-2">
                          {item.quantity ? `${item.quantity} ${item.unit ?? ""}`.trim() : item.amount ? `Amount ${item.amount}${doc.document?.currency ? ` ${doc.document.currency}` : ""}` : "No quantity"}
                          {item.page > 1 || (doc.document?.line_items.some((l) => l.page > 1) ?? false) ? `, page ${item.page}` : ""}
                        </div>
                      </div>
                      <div className="shrink-0 text-right">
                        {item.is_activity ? (
                          <div className="num text-sm font-medium text-ink">
                            {result?.kg_co2e ? kgFmt.format(Number(result.kg_co2e)) : "Not calculated"}
                            {result?.kg_co2e ? <span className="text-xs font-normal text-ink-2"> kg CO2e</span> : null}
                          </div>
                        ) : (
                          <div className="text-xs">Charge, not counted</div>
                        )}
                      </div>
                    </div>
                    {item.is_activity && result ? (
                      <div className="mt-1.5 space-y-0.5 text-xs text-ink-2">
                        <div>
                          {result.factor_name ?? "No factor matched"}
                          {source ? `, ${source}` : ""}
                        </div>
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5">
                          {scope ? (
                            <span className="inline-flex items-center gap-1.5">
                              <span className="h-2 w-2 rounded-sm" style={{ background: scope.color }} aria-hidden="true" />
                              {scope.label}
                            </span>
                          ) : null}
                          <span>{methodLabel[result.method] ?? result.method}</span>
                          {trace?.kgco2e_per_unit ? <span className="num">{trace.kgco2e_per_unit} kg per {trace.factor_unit}</span> : null}
                        </div>
                      </div>
                    ) : null}
                  </button>
                </li>
              );
            })}
          </ul>
        </section>

        <details className="rounded-[10px] border border-rule bg-surface">
          <summary className="cursor-pointer px-5 py-4 text-base font-medium">Audit trail</summary>
          <ol className="border-t border-rule">
            {doc.audit.map((a, i) => (
              <li key={i} className="border-b border-rule px-5 py-3 text-sm last:border-b-0">
                <div className="flex justify-between gap-4">
                  <span className="font-medium">{eventLabel[a.event] ?? a.event}</span>
                  <span className="num text-ink-2">{when.format(new Date(a.at))} UTC</span>
                </div>
                <div className="break-words text-xs text-ink-2">{detailText(a.detail_json)}</div>
              </li>
            ))}
          </ol>
        </details>
      </div>
    </div>
  );
}
