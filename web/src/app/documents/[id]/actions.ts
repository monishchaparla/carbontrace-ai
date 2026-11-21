"use server";

import { revalidatePath } from "next/cache";
import { apiFetch } from "@/lib/api";

export async function markReviewed(id: string): Promise<{ ok: boolean; message?: string }> {
  try {
    const res = await apiFetch(`/documents/${encodeURIComponent(id)}/review`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ note: "" }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      return { ok: false, message: typeof data.detail === "string" ? data.detail : "Couldn't mark this document reviewed." };
    }
  } catch {
    return { ok: false, message: "The API is not reachable." };
  }
  revalidatePath("/", "layout");
  return { ok: true };
}
