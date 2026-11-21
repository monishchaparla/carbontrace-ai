// Placeholder data for the dashboard until the extraction pipeline is connected.
// Shapes match what the API will return, so components do not change later.

export type Scope = 1 | 2 | 3;

export const scopeMeta: Record<Scope, { label: string; detail: string; color: string }> = {
  1: { label: "Scope 1", detail: "Direct fuel", color: "var(--scope-1)" },
  2: { label: "Scope 2", detail: "Electricity", color: "var(--scope-2)" },
  3: { label: "Scope 3", detail: "Value chain", color: "var(--scope-3)" },
};

export type MonthPoint = { month: string; s1: number; s2: number; s3: number };

export const monthly: MonthPoint[] = [
  { month: "Apr", s1: 34, s2: 61, s3: 98 },
  { month: "May", s1: 36, s2: 64, s3: 112 },
  { month: "Jun", s1: 33, s2: 70, s3: 121 },
  { month: "Jul", s1: 38, s2: 72, s3: 129 },
  { month: "Aug", s1: 35, s2: 66, s3: 108 },
  { month: "Sep", s1: 36, s2: 64, s3: 107 },
];

// Change against the previous six months, as a fraction.
export const change: Record<Scope, number> = { 1: -0.041, 2: 0.026, 3: 0.063 };

export type Source = { name: string; site: string; scope: Scope; tonnes: number };

export const topSources: Source[] = [
  { name: "Road freight", site: "Pune to Mumbai lane", scope: 3, tonnes: 318 },
  { name: "Grid electricity", site: "Plant 2, Chakan", scope: 2, tonnes: 247 },
  { name: "Hot-rolled steel coil", site: "Purchased goods", scope: 3, tonnes: 201 },
  { name: "Grid electricity", site: "Head office, Pune", scope: 2, tonnes: 150 },
  { name: "Diesel generators", site: "Plant 1, Bhosari", scope: 1, tonnes: 126 },
];

export type DocStatus = "verified" | "review" | "failed";

export type DocItem = { name: string; kind: string; date: string; status: DocStatus; note?: string };

export const recentDocs: DocItem[] = [
  { name: "MSEDCL bill, September", kind: "Electricity bill", date: "Oct 4", status: "verified" },
  { name: "Steel invoice 4471", kind: "Supplier invoice", date: "Oct 3", status: "review", note: "Unit reads MWh, expected kWh" },
  { name: "Freight manifest 88", kind: "Logistics manifest", date: "Oct 2", status: "review", note: "Date range spans 14 months" },
  { name: "Diesel purchase, August", kind: "Fuel receipt", date: "Sep 29", status: "verified" },
  { name: "Scanned courier slip", kind: "Image upload", date: "Sep 28", status: "failed", note: "Text could not be read" },
];

export const reviewCount = recentDocs.filter((d) => d.status === "review").length;
