"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { IconUpload } from "@tabler/icons-react";

type Item = { key: string; name: string; text: string; id?: string; done?: boolean; error?: boolean };

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function passcode(): string {
  try {
    return sessionStorage.getItem("uploadPasscode") ?? "";
  } catch {
    return "";
  }
}

export function UploadButton({ variant = "primary" }: { variant?: "primary" | "secondary" }) {
  const input = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const [items, setItems] = useState<Item[]>([]);

  const patch = (key: string, p: Partial<Item>) => setItems((all) => all.map((i) => (i.key === key ? { ...i, ...p } : i)));

  async function send(file: File, key: string) {
    try {
      const body = new FormData();
      body.append("file", file);
      const post = () => fetch("/api/upload", { method: "POST", body, headers: { "x-upload-passcode": passcode() } });
      let res = await post();
      let data = await res.json().catch(() => ({}));
      if (data.code === "passcode_required") {
        const entered = window.prompt("Enter the upload passcode for this demo");
        if (entered) {
          try {
            sessionStorage.setItem("uploadPasscode", entered);
          } catch {}
          res = await post();
          data = await res.json().catch(() => ({}));
        }
      }
      if (!res.ok) return patch(key, { text: typeof data.detail === "string" ? data.detail : "Upload failed.", error: true });
      if (data.duplicate) return patch(key, { text: "Already uploaded", id: data.id, done: true });
      patch(key, { text: "Processing…", id: data.id });
      for (let i = 0; i < 60; i++) {
        await sleep(2000);
        const s = await fetch(`/api/upload?id=${encodeURIComponent(data.id)}`).then((r) => r.json()).catch(() => ({}));
        if (s.status === "done") {
          router.refresh();
          return patch(key, { text: "Added", done: true });
        }
        if (s.status === "failed") {
          router.refresh();
          return patch(key, { text: "Couldn't read this file.", error: true });
        }
      }
      patch(key, { text: "Still processing. Check Documents shortly." });
    } catch {
      patch(key, { text: "Upload failed.", error: true });
    }
  }

  function pick(files: FileList | null) {
    if (!files?.length) return;
    const batch = Array.from(files).map((f, i) => ({ f, key: `${Date.now()}-${i}` }));
    setItems(batch.map(({ f, key }) => ({ key, name: f.name, text: "Uploading…" })));
    batch.forEach(({ f, key }) => void send(f, key));
    if (input.current) input.current.value = "";
  }

  const cls =
    variant === "primary"
      ? "bg-pine text-on-pine hover:opacity-90"
      : "border border-rule bg-surface text-ink hover:bg-canvas";

  return (
    <div className="relative">
      <input
        ref={input}
        type="file"
        multiple
        hidden
        accept="application/pdf,image/png,image/jpeg,image/webp"
        onChange={(e) => pick(e.target.files)}
      />
      <button
        type="button"
        onClick={() => input.current?.click()}
        className={`inline-flex h-10 items-center gap-2 rounded-md px-4 text-sm font-medium ${cls}`}
      >
        <IconUpload size={18} stroke={1.75} aria-hidden="true" />
        Upload documents
      </button>
      <ul
        aria-live="polite"
        className={items.length ? "absolute right-0 top-12 z-10 w-80 max-w-[calc(100vw-2rem)] rounded-[10px] border border-rule bg-surface p-3 text-sm" : "sr-only"}
      >
        {items.map((i) => (
          <li key={i.key} className="py-1">
            <div className="truncate font-medium">{i.name}</div>
            <div className={i.error ? "text-fail" : "text-ink-2"}>
              {i.text}
              {i.done && i.id ? (
                <>
                  {" "}
                  <Link href={`/documents/${i.id}`} className="font-medium text-pine underline">
                    Open document
                  </Link>
                </>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
