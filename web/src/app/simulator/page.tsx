import { IconAdjustmentsHorizontal } from "@tabler/icons-react";

export const metadata = { title: "What-if simulator | CarbonTrace AI" };

export default function Simulator() {
  return (
    <div className="mx-auto max-w-[1180px] px-4 py-6 sm:px-8 sm:py-8">
      <header>
        <h1 className="text-[28px] font-semibold tracking-tight">What-if simulator</h1>
        <p className="mt-1 text-sm text-ink-2">Test how a change in suppliers, fuel or electricity source would move your totals.</p>
      </header>
      <section className="mt-6 rounded-[10px] border border-rule bg-surface px-6 py-12 text-center">
        <IconAdjustmentsHorizontal size={28} stroke={1.5} className="mx-auto text-ink-2" aria-hidden="true" />
        <h2 className="mt-3 text-base font-medium">Coming next</h2>
        <p className="mx-auto mt-1 max-w-md text-sm text-ink-2">The simulator is not built yet, so there are no scenarios to show.</p>
      </section>
    </div>
  );
}
