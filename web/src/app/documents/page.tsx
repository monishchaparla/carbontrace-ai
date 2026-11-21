import Link from "next/link";
import { IconFileText } from "@tabler/icons-react";
import { UploadButton } from "@/components/upload-button";
import { getDocument, getDocuments } from "@/lib/api";
import { docStatus, docTypeLabel, nf, periodText, statusStyle } from "@/lib/format";

export const metadata = { title: "Documents | CarbonTrace AI" };

export default async function Documents() {
  const docs = (await getDocuments()) ?? [];
  // The list route carries no totals, so read each processed document. Fine at demo scale.
  const details = await Promise.all(docs.map((d) => (d.status === "done" ? getDocument(d.id) : null)));
  const totals = details.map((d) => (d ? d.lines.reduce((s, l) => s + (l.kg_co2e ? Number(l.kg_co2e) : 0), 0) / 1000 : null));

  return (
    <div className="mx-auto max-w-[1180px] px-4 py-6 sm:px-8 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-semibold tracking-tight">Documents</h1>
          <p className="mt-1 text-sm text-ink-2">Every bill and invoice, with its emissions total.</p>
        </div>
        <UploadButton />
      </header>

      {docs.length === 0 ? (
        <section className="mt-6 rounded-[10px] border border-rule bg-surface px-6 py-12 text-center">
          <IconFileText size={28} stroke={1.5} className="mx-auto text-ink-2" aria-hidden="true" />
          <h2 className="mt-3 text-base font-medium">No documents yet</h2>
          <p className="mx-auto mt-1 max-w-md text-sm text-ink-2">
            Upload an electricity bill, fuel receipt, freight invoice or supplier invoice. PDF, PNG, JPEG and WebP files work.
          </p>
        </section>
      ) : (
        <section aria-label="All documents" className="mt-6 overflow-x-auto rounded-[10px] border border-rule bg-surface">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="text-left text-ink-2">
                <th className="px-5 py-3 font-medium">Document</th>
                <th className="px-2 py-3 font-medium">Type</th>
                <th className="px-2 py-3 font-medium">Supplier</th>
                <th className="px-2 py-3 font-medium">Period</th>
                <th className="px-2 py-3 font-medium">Status</th>
                <th className="px-5 py-3 text-right font-medium">tCO2e</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d, i) => {
                const st = statusStyle[docStatus(d)];
                return (
                  <tr key={d.id} className="h-11 border-t border-rule hover:bg-canvas">
                    <td className="px-5 py-2 font-medium">
                      <Link href={`/documents/${d.id}`} className="hover:underline">
                        {d.filename}
                      </Link>
                    </td>
                    <td className="px-2 text-ink-2">{docTypeLabel(d.document?.doc_type)}</td>
                    <td className="px-2 text-ink-2">{d.document?.supplier ?? "Unknown"}</td>
                    <td className="px-2 text-ink-2">{periodText(d.document)}</td>
                    <td className="px-2">
                      <span className={`inline-block rounded-full px-2.5 text-xs leading-[22px] ${st.cls}`}>{st.label}</span>
                    </td>
                    <td className="num px-5 text-right font-medium">{totals[i] === null ? "None" : nf.format(totals[i]!)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
