import Link from "next/link";
import { IconCircleCheck } from "@tabler/icons-react";
import { getDocuments } from "@/lib/api";
import { docTypeLabel } from "@/lib/format";

export const metadata = { title: "Review | CarbonTrace AI" };

export default async function Review() {
  const docs = ((await getDocuments()) ?? []).filter((d) => d.status === "done" && d.needs_review);
  return (
    <div className="mx-auto max-w-[1180px] px-4 py-6 sm:px-8 sm:py-8">
      <header>
        <h1 className="text-[28px] font-semibold tracking-tight">Review</h1>
        <p className="mt-1 text-sm text-ink-2">Documents where the extraction or the factor match needs a second look.</p>
      </header>
      {docs.length === 0 ? (
        <section className="mt-6 rounded-[10px] border border-rule bg-surface px-6 py-12 text-center">
          <IconCircleCheck size={28} stroke={1.5} className="mx-auto text-pine" aria-hidden="true" />
          <h2 className="mt-3 text-base font-medium">Nothing to review</h2>
          <p className="mt-1 text-sm text-ink-2">Documents that need a check will appear here.</p>
        </section>
      ) : (
        <ul className="mt-6 space-y-4">
          {docs.map((d) => (
            <li key={d.id} className="rounded-[10px] border border-rule bg-surface p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-base font-medium">{d.filename}</h2>
                  <p className="text-sm text-ink-2">
                    {docTypeLabel(d.document?.doc_type)}
                    {d.document?.supplier ? `, ${d.document.supplier}` : ""}
                  </p>
                </div>
                <Link
                  href={`/documents/${d.id}`}
                  className="inline-flex h-10 items-center rounded-md bg-pine px-4 text-sm font-medium text-on-pine hover:opacity-90"
                >
                  Review item
                </Link>
              </div>
              <ul className="mt-3 space-y-1 text-sm">
                {d.flags.map((f, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-review-ink" aria-hidden="true" />
                    <span>{f.message}</span>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
