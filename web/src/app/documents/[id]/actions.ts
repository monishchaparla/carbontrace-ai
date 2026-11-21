"use server";

import { revalidatePath } from "next/cache";
import { apiFetch } from "@/lib/api";
import { passcodeOk } from "@/lib/passcode";

export async function markReviewed(id: string, passcode = ""): Promise<{ ok: boolean; message?: string; code?: string }> {
  if (!passcodeOk(passcode)) {
    return { ok: false, message: "Marking documents reviewed needs the demo passcode.", code: "passcode_required" };
  }
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
