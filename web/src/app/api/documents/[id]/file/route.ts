import { apiFetch } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const res = await apiFetch(`/documents/${encodeURIComponent(id)}/file`);
    if (!res.ok || !res.body) return new Response("Not found", { status: res.status || 502 });
    return new Response(res.body, {
      headers: { "content-type": res.headers.get("content-type") ?? "application/octet-stream", "cache-control": "private, no-store" },
    });
  } catch {
    return new Response("The API is not reachable.", { status: 502 });
  }
}
