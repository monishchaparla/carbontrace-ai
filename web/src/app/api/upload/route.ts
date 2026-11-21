import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";
import { passcodeOk } from "@/lib/passcode";

export const dynamic = "force-dynamic";

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
