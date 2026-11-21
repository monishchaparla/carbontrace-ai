import type { DocSummary } from "@/lib/api";

export type Status = "verified" | "review" | "failed" | "processing";

export const statusStyle: Record<Status, { label: string; cls: string }> = {
  verified: { label: "Verified", cls: "bg-pine-wash text-pine" },
  review: { label: "Needs review", cls: "bg-review-wash text-review-ink" },
  failed: { label: "Couldn't read", cls: "bg-fail-wash text-fail" },
  processing: { label: "Processing", cls: "border border-rule text-ink-2" },
};

export function docStatus(d: Pick<DocSummary, "status" | "needs_review">): Status {
  if (d.status === "failed") return "failed";
  if (d.status === "processing") return "processing";
  return d.needs_review ? "review" : "verified";
}

const types: Record<string, string> = {
  electricity_bill: "Electricity bill",
  fuel_receipt: "Fuel receipt",
  freight_invoice: "Freight invoice",
  supplier_invoice: "Supplier invoice",
  travel_invoice: "Travel invoice",
  other: "Other document",
};
export const docTypeLabel = (t?: string | null) => (t ? (types[t] ?? "Other document") : "Not read yet");

const utc = (o: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat("en-GB", { ...o, timeZone: "UTC" });
const fMonth = utc({ month: "short" });
const fMonthYear = utc({ month: "short", year: "numeric" });
const fDayMonth = utc({ day: "numeric", month: "short" });
const fFull = utc({ day: "numeric", month: "short", year: "numeric" });

const ym = (s: string) => new Date(`${s}-01T00:00:00Z`);
export const monthLabel = (s: string) => (isNaN(+ym(s)) ? s : fMonth.format(ym(s)));
export const monthYearLabel = (s: string) => (isNaN(+ym(s)) ? s : fMonthYear.format(ym(s)));

export function dateLabel(iso?: string | null): string {
  const d = iso ? new Date(iso) : null;
  return d && !isNaN(+d) ? fFull.format(d) : "No date";
}
export function shortDate(iso: string): string {
  const d = new Date(iso);
  return isNaN(+d) ? "" : fDayMonth.format(d);
}

export function periodText(d: DocSummary["document"]): string {
  if (!d) return "No period";
  if (d.period_start && d.period_end) return `${dateLabel(d.period_start)} to ${dateLabel(d.period_end)}`;
  return d.invoice_date ? dateLabel(d.invoice_date) : "No period";
}

export const nf = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });
export const kgFmt = new Intl.NumberFormat("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
