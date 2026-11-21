"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MonthPoint } from "@/lib/sample-data";

type TipProps = { active?: boolean; label?: string; payload?: { dataKey: string; value: number }[] };

const names: Record<string, string> = { s1: "Scope 1", s2: "Scope 2", s3: "Scope 3" };
const colors: Record<string, string> = { s1: "var(--scope-1)", s2: "var(--scope-2)", s3: "var(--scope-3)" };

function Tip({ active, label, payload }: TipProps) {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((sum, p) => sum + p.value, 0);
  return (
    <div className="min-w-44 rounded-[10px] border border-rule bg-surface px-3 py-2.5 text-sm">
      <div className="mb-1.5 font-medium">{label}</div>
      {[...payload].reverse().map((p) => (
        <div key={p.dataKey} className="flex items-center gap-2 py-0.5">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: colors[p.dataKey] }} />
          <span className="flex-1 text-ink-2">{names[p.dataKey]}</span>
          <span className="num">{p.value} t</span>
        </div>
      ))}
      <div className="mt-1.5 flex border-t border-rule pt-1.5 font-medium">
        <span className="flex-1">Total</span>
        <span className="num">{total} t</span>
      </div>
    </div>
  );
}

export function EmissionsChart({ data }: { data: MonthPoint[] }) {
  return (
    <div className="h-[300px] w-full" role="img" aria-label="Monthly emissions stacked by scope, April to September">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: -12 }} barCategoryGap="28%">
          <CartesianGrid vertical={false} stroke="var(--rule)" />
          <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: "var(--ink-2)", fontSize: 13 }} dy={6} />
          <YAxis tickLine={false} axisLine={false} tick={{ fill: "var(--ink-2)", fontSize: 12 }} width={48} />
          <Tooltip content={<Tip />} cursor={{ fill: "var(--pine-wash)", opacity: 0.6 }} />
          <Bar dataKey="s1" stackId="e" fill="var(--scope-1)" stroke="var(--surface)" strokeWidth={2} isAnimationActive={false} />
          <Bar dataKey="s2" stackId="e" fill="var(--scope-2)" stroke="var(--surface)" strokeWidth={2} isAnimationActive={false} />
          <Bar dataKey="s3" stackId="e" fill="var(--scope-3)" stroke="var(--surface)" strokeWidth={2} radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
