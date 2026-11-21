import { createHash, timingSafeEqual } from "node:crypto";
import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

export const dynamic = "force-dynamic";

// Public deployments set UPLOAD_PASSCODE so visitors can browse but not spend the extraction quota.
function passcodeOk(given: string | null): boolean {
  const expected = process.env.UPLOAD_PASSCODE;
  if (!expected) return true;
  const hash = (s: string) => createHash("sha256").update(s).digest();
  return timingSafeEqual(hash(given ?? ""), hash(expected));
}

export async function POST(req: Request) {
  if (!passcodeOk(req.headers.get("x-upload-passcode"))) {
    return NextResponse.json({ detail: "Uploads need a passcode in this demo.", code: "passcode_required" }, { status: 401 });
  }
  const file = (await req.formData().catch(() => null))?.get("file");
  if (!(file instanceof File)) return NextResponse.json({ detail: "No file received." }, { status: 400 });
  const body = new FormData();
  body.append("file", file, file.name);
  try {
    const res = await apiFetch("/documents", { method: "POST", body });
    const data = await res.json().catch(() => ({ detail: "Unexpected response from the API." }));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ detail: "The API is not reachable." }, { status: 502 });
  }
}

// Status poll for a document just uploaded.
export async function GET(req: Request) {
  const id = new URL(req.url).searchParams.get("id") ?? "";
  try {
    const res = await apiFetch(`/documents/${encodeURIComponent(id)}`);
    if (!res.ok) return NextResponse.json({ status: "unknown" }, { status: res.status });
    const d = await res.json();
    return NextResponse.json({ status: d.status });
  } catch {
    return NextResponse.json({ status: "unknown" }, { status: 502 });
  }
}
