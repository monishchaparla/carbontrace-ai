import Link from "next/link";
import { notFound } from "next/navigation";
import { IconArrowLeft } from "@tabler/icons-react";
import { AuditView } from "@/components/audit-view";
import { getDocument } from "@/lib/api";
import { docStatus, docTypeLabel, nf, periodText, statusStyle } from "@/lib/format";

export const dynamic = "force-dynamic";

const mimes: Record<string, string> = { pdf: "application/pdf" };

export default async function DocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const doc = await getDocument(id);
  if (!doc) notFound();
  const st = statusStyle[docStatus(doc)];
  const tonnes = doc.lines.reduce((s, l) => s + (l.kg_co2e ? Number(l.kg_co2e) : 0), 0) / 1000;
  const mime = doc.filename.toLowerCase().endsWith(".pdf") ? mimes.pdf : "image/*";
  const d = doc.document;

  return (
    <div className="mx-auto max-w-[1440px] px-4 py-6 sm:px-8 sm:py-8">
      <Link href="/documents" className="inline-flex items-center gap-1 text-sm text-ink-2 hover:text-ink">
        <IconArrowLeft size={16} aria-hidden="true" />
        Documents
      </Link>
      <header className="mt-3 flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="truncate text-[28px] font-semibold tracking-tight">{doc.filename}</h1>
            <span className={`rounded-full px-2.5 text-xs leading-[22px] ${st.cls}`}>{st.label}</span>
          </div>
          <p className="mt-1 text-sm text-ink-2">
            {docTypeLabel(d?.doc_type)}
            {d?.supplier ? `, ${d.supplier}` : ""}
            {d?.invoice_number ? `, invoice ${d.invoice_number}` : ""}. {periodText(d)}.
          </p>
        </div>
        <div className="num text-ink-2">
          <span className="text-[40px] font-semibold leading-none tracking-tight text-ink">{nf.format(tonnes)}</span>
          <span className="ml-1.5 text-sm">tCO2e</span>
        </div>
      </header>
      <AuditView doc={doc} fileUrl={`/api/documents/${encodeURIComponent(doc.id)}/file`} mime={mime} />
    </div>
  );
}
