export const metadata = { title: "Emission factors | CarbonTrace AI" };

const sources = [
  { name: "US EPA", version: "v1.3.0", count: "1,016" },
  { name: "UK DESNZ", version: "2026", count: "2,622" },
  { name: "India CEA", version: "v22.0", count: "1" },
];

export default function Factors() {
  return (
    <div className="mx-auto max-w-[1180px] px-4 py-6 sm:px-8 sm:py-8">
      <header>
        <h1 className="text-[28px] font-semibold tracking-tight">Emission factor library</h1>
        <p className="mt-1 text-sm text-ink-2">Every calculation cites one of these sources. Browsing and search are coming next.</p>
      </header>
      <section aria-label="Sources" className="mt-6 rounded-[10px] border border-rule bg-surface">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-ink-2">
              <th className="px-5 py-3 font-medium">Source</th>
              <th className="px-2 py-3 font-medium">Version</th>
              <th className="px-5 py-3 text-right font-medium">Factors</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.name} className="h-11 border-t border-rule">
                <td className="px-5 py-2 font-medium">{s.name}</td>
                <td className="px-2 text-ink-2">{s.version}</td>
                <td className="num px-5 text-right font-medium">{s.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
