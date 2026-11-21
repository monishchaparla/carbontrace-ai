import Link from "next/link";
import { IconArrowDownRight, IconArrowUpRight } from "@tabler/icons-react";
import { EmissionsChart } from "@/components/emissions-chart";
import { UploadButton } from "@/components/upload-button";
import { getDocuments, getSummary } from "@/lib/api";
import { docStatus, docTypeLabel, monthLabel, monthYearLabel, shortDate, statusStyle } from "@/lib/format";
import { change, monthly as sampleMonthly, recentDocs, scopeMeta, topSources as sampleSources, type DocStatus, type MonthPoint, type Scope } from "@/lib/sample-data";

const fmt = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 3 });

type Totals = Record<Scope, number>;
type RecentDoc = { id?: string; name: string; kind: string; date: string; status: keyof typeof statusStyle; note?: string };

const sampleStatus: Record<DocStatus, keyof typeof statusStyle> = { verified: "verified", review: "review", failed: "failed" };

function ScopeTotal({ scope, totals, grand, delta }: { scope: Scope; totals: Totals; grand: number; delta?: number }) {
  const meta = scopeMeta[scope];
  const share = grand ? totals[scope] / grand : 0;
  const Arrow = delta !== undefined && delta < 0 ? IconArrowDownRight : IconArrowUpRight;
  return (
    <div className="border-t border-rule pt-4">
      <div className="flex items-center gap-2 text-sm text-ink-2">
        <span className="h-2.5 w-2.5 rounded-sm" style={{ background: meta.color }} aria-hidden="true" />
        <span className="font-medium text-ink">{meta.label}</span>
        <span>{meta.detail}</span>
      </div>
      <div className="num mt-2 text-2xl font-semibold tracking-tight">
        {fmt.format(totals[scope])} <span className="text-sm font-normal text-ink-2">tCO2e</span>
      </div>
      <div className="mt-1 flex items-center gap-3 text-sm text-ink-2">
        <span className="num">{Math.round(share * 100)}% of total</span>
        {delta !== undefined ? (
          <span className={`num inline-flex items-center gap-0.5 ${delta < 0 ? "text-pine" : "text-review-ink"}`}>
            <Arrow size={14} aria-hidden="true" />
            {Math.abs(delta * 100).toFixed(1)}%
            <span className="sr-only">{delta < 0 ? "lower" : "higher"} than the previous six months</span>
          </span>
        ) : null}
      </div>
    </div>
  );
}

export default async function Overview() {
  const [summary, documents] = await Promise.all([getSummary(), getDocuments()]);
  const real = !!summary && summary.documents > 0;

  let monthly: MonthPoint[] = sampleMonthly;
  let topSources = sampleSources;
  let period = "April to September 2026, all sites";
  let span = "in six months";
  let recent: RecentDoc[] = recentDocs.map((d) => ({ ...d, status: sampleStatus[d.status] }));
  if (real) {
    monthly = summary.monthly.map((m) => ({ ...m, month: monthLabel(m.month) }));
    topSources = summary.top_sources;
    const first = summary.monthly[0]?.month;
    const last = summary.monthly.at(-1)?.month;
    period = !first ? "No processed documents yet" : first === last ? monthYearLabel(first) : `${monthYearLabel(first)} to ${monthYearLabel(last!)}`;
    span = "in total";
    recent = (documents ?? []).slice(0, 5).map((d) => ({
      id: d.id,
      name: d.filename,
      kind: docTypeLabel(d.document?.doc_type),
      date: shortDate(d.uploaded_at),
      status: docStatus(d),
      note: d.status === "failed" ? "Text could not be read" : d.flags[0]?.message,
    }));
  }
  const totals: Totals = {
    1: monthly.reduce((s, m) => s + m.s1, 0),
    2: monthly.reduce((s, m) => s + m.s2, 0),
    3: monthly.reduce((s, m) => s + m.s3, 0),
  };
  const grand = totals[1] + totals[2] + totals[3];

  return (
    <div className="mx-auto max-w-[1180px] px-4 py-6 sm:px-8 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-[28px] font-semibold tracking-tight">Overview</h1>
            <span className="rounded-full border border-rule px-2.5 text-xs leading-6 text-ink-2">{real ? "Your workspace" : "Sample workspace"}</span>
          </div>
          <p className="mt-1 text-sm text-ink-2">{period}</p>
        </div>
        <div className="flex items-center gap-2">
          {real ? null : (
            <>
              <label className="sr-only" htmlFor="period">Reporting period</label>
              <select id="period" defaultValue="h1" className="h-10 rounded-md border border-rule bg-surface px-3 text-sm text-ink">
                <option value="h1">Apr to Sep 2026</option>
                <option value="q2">Jul to Sep 2026</option>
                <option value="fy">FY 2025 to 26</option>
              </select>
            </>
          )}
          <UploadButton />
        </div>
      </header>

      <section aria-labelledby="trend" className="mt-6 rounded-[10px] border border-rule bg-surface p-5 sm:p-6">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="trend" className="text-base font-medium">Emissions by month</h2>
          <div className="num text-ink-2">
            <span className="text-[40px] font-semibold leading-none tracking-tight text-ink">{fmt.format(grand)}</span>
            <span className="ml-1.5 text-sm">tCO2e {span}</span>
          </div>
        </div>
        <div className="mt-4">
          <EmissionsChart data={monthly} />
        </div>
        <div className="mt-2 grid gap-6 sm:grid-cols-3">
          <ScopeTotal scope={1} totals={totals} grand={grand} delta={real ? undefined : change[1]} />
          <ScopeTotal scope={2} totals={totals} grand={grand} delta={real ? undefined : change[2]} />
          <ScopeTotal scope={3} totals={totals} grand={grand} delta={real ? undefined : change[3]} />
        </div>
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
        <section aria-labelledby="sources" className="rounded-[10px] border border-rule bg-surface">
          <h2 id="sources" className="px-5 pt-5 text-base font-medium">Largest sources</h2>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="text-left text-ink-2">
                <th className="px-5 pb-2 font-medium">Source</th>
                <th className="px-2 pb-2 font-medium">Scope</th>
                <th className="px-5 pb-2 text-right font-medium">tCO2e</th>
              </tr>
            </thead>
            <tbody>
              {topSources.map((s) => (
                <tr key={s.name + s.site} className="h-11 border-t border-rule hover:bg-canvas">
                  <td className="px-5 py-2">
                    <div className="font-medium">{s.name}</div>
                    <div className="text-xs text-ink-2">{s.site}</div>
                  </td>
                  <td className="px-2">
                    <span className="inline-flex items-center gap-1.5 text-ink-2">
                      <span className="h-2 w-2 rounded-sm" style={{ background: scopeMeta[s.scope].color }} aria-hidden="true" />
                      {s.scope}
                    </span>
                  </td>
                  <td className="num px-5 text-right font-medium">{fmt.format(s.tonnes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section aria-labelledby="docs" className="rounded-[10px] border border-rule bg-surface">
          <h2 id="docs" className="px-5 pt-5 text-base font-medium">Recent documents</h2>
          <ul className="mt-3">
            {recent.length === 0 ? <li className="border-t border-rule px-5 py-3 text-sm text-ink-2">No documents yet. Upload a bill or invoice to begin.</li> : null}
            {recent.map((d) => (
              <li key={d.name} className="flex items-start gap-3 border-t border-rule px-5 py-3">
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">
                    {d.id ? <Link href={`/documents/${d.id}`} className="hover:underline">{d.name}</Link> : d.name}
                  </div>
                  <div className="text-xs text-ink-2">
                    {d.kind}, {d.date}
                  </div>
                  {d.note ? <div className="mt-1 text-xs text-ink-2">{d.note}</div> : null}
                </div>
                <span className={`shrink-0 rounded-full px-2.5 text-xs leading-[22px] ${statusStyle[d.status].cls}`}>
                  {statusStyle[d.status].label}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
