import { IconUpload, IconArrowDownRight, IconArrowUpRight } from "@tabler/icons-react";
import { EmissionsChart } from "@/components/emissions-chart";
import { change, monthly, recentDocs, scopeMeta, topSources, type DocStatus, type Scope } from "@/lib/sample-data";

const totals: Record<Scope, number> = {
  1: monthly.reduce((s, m) => s + m.s1, 0),
  2: monthly.reduce((s, m) => s + m.s2, 0),
  3: monthly.reduce((s, m) => s + m.s3, 0),
};
const grand = totals[1] + totals[2] + totals[3];
const fmt = new Intl.NumberFormat("en-IN");

const statusStyle: Record<DocStatus, { label: string; cls: string }> = {
  verified: { label: "Verified", cls: "bg-pine-wash text-pine" },
  review: { label: "Needs review", cls: "bg-review-wash text-review-ink" },
  failed: { label: "Couldn't read", cls: "bg-fail-wash text-fail" },
};

function ScopeTotal({ scope }: { scope: Scope }) {
  const meta = scopeMeta[scope];
  const delta = change[scope];
  const share = totals[scope] / grand;
  const Arrow = delta < 0 ? IconArrowDownRight : IconArrowUpRight;
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
        <span className={`num inline-flex items-center gap-0.5 ${delta < 0 ? "text-pine" : "text-review-ink"}`}>
          <Arrow size={14} aria-hidden="true" />
          {Math.abs(delta * 100).toFixed(1)}%
          <span className="sr-only">{delta < 0 ? "lower" : "higher"} than the previous six months</span>
        </span>
      </div>
    </div>
  );
}

export default function Overview() {
  return (
    <div className="mx-auto max-w-[1180px] px-4 py-6 sm:px-8 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-[28px] font-semibold tracking-tight">Overview</h1>
            <span className="rounded-full border border-rule px-2.5 text-xs leading-6 text-ink-2">Sample workspace</span>
          </div>
          <p className="mt-1 text-sm text-ink-2">April to September 2026, all sites</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="sr-only" htmlFor="period">Reporting period</label>
          <select id="period" defaultValue="h1" className="h-10 rounded-md border border-rule bg-surface px-3 text-sm text-ink">
            <option value="h1">Apr to Sep 2026</option>
            <option value="q2">Jul to Sep 2026</option>
            <option value="fy">FY 2025 to 26</option>
          </select>
          <button className="inline-flex h-10 items-center gap-2 rounded-md bg-pine px-4 text-sm font-medium text-on-pine hover:opacity-90">
            <IconUpload size={18} stroke={1.75} aria-hidden="true" />
            Upload documents
          </button>
        </div>
      </header>

      <section aria-labelledby="trend" className="mt-6 rounded-[10px] border border-rule bg-surface p-5 sm:p-6">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="trend" className="text-base font-medium">Emissions by month</h2>
          <div className="num text-ink-2">
            <span className="text-[40px] font-semibold leading-none tracking-tight text-ink">{fmt.format(grand)}</span>
            <span className="ml-1.5 text-sm">tCO2e in six months</span>
          </div>
        </div>
        <div className="mt-4">
          <EmissionsChart data={monthly} />
        </div>
        <div className="mt-2 grid gap-6 sm:grid-cols-3">
          <ScopeTotal scope={1} />
          <ScopeTotal scope={2} />
          <ScopeTotal scope={3} />
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
            {recentDocs.map((d) => (
              <li key={d.name} className="flex items-start gap-3 border-t border-rule px-5 py-3">
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{d.name}</div>
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
