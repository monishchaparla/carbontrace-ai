"use client";

import { useEffect, useRef, useState } from "react";
import type { PDFDocumentProxy } from "pdfjs-dist";

export type Highlight = { page: number; box: [number, number, number, number] } | null;

type PageSize = { w: number; h: number };

function Frame({ n, size, highlight, image, children }: { n: number; size: PageSize | null; highlight: Highlight; image?: boolean; children?: React.ReactNode }) {
  const mark = useRef<HTMLDivElement>(null);
  const on = highlight && highlight.page === n ? highlight : null;

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    mark.current?.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
  }, [on?.box.join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div
      className="relative mx-auto w-full overflow-hidden rounded-md border border-rule bg-white"
      style={image ? undefined : { aspectRatio: size ? `${size.w} / ${size.h}` : "3 / 4" }}
      data-page={n}
    >
      {children}
      {on ? (
        <div
          ref={mark}
          aria-hidden="true"
          className="pointer-events-none absolute rounded-sm border-2 border-pine"
          style={{
            top: `${on.box[0] / 10}%`,
            left: `${on.box[1] / 10}%`,
            height: `${(on.box[2] - on.box[0]) / 10}%`,
            width: `${(on.box[3] - on.box[1]) / 10}%`,
            background: "color-mix(in srgb, var(--pine) 18%, transparent)",
          }}
        />
      ) : null}
    </div>
  );
}

function PdfPage({ pdf, n, width, highlight }: { pdf: PDFDocumentProxy; n: number; width: number; highlight: Highlight }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [size, setSize] = useState<PageSize | null>(null);

  useEffect(() => {
    let task: { cancel: () => void; promise: Promise<unknown> } | null = null;
    let dead = false;
    pdf.getPage(n).then((page) => {
      if (dead || !canvas.current) return;
      const base = page.getViewport({ scale: 1 });
      setSize({ w: base.width, h: base.height });
      if (!width) return;
      const dpr = window.devicePixelRatio || 1;
      const viewport = page.getViewport({ scale: (width / base.width) * dpr });
      canvas.current.width = viewport.width;
      canvas.current.height = viewport.height;
      task = page.render({ canvas: canvas.current, viewport });
      task.promise.catch(() => {});
    });
    return () => {
      dead = true;
      task?.cancel();
    };
  }, [pdf, n, width]);

  return (
    <Frame n={n} size={size} highlight={highlight}>
      <canvas ref={canvas} className="absolute inset-0 h-full w-full" aria-label={`Page ${n} of the source document`} role="img" />
    </Frame>
  );
}

export function SourcePages({ src, mime, highlight }: { src: string; mime: string; highlight: Highlight }) {
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null);
  const [error, setError] = useState(false);
  const isPdf = mime === "application/pdf";

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setWidth(Math.round(el.clientWidth)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (!isPdf) return;
    let dead = false;
    let doc: PDFDocumentProxy | null = null;
    (async () => {
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();
        doc = await pdfjs.getDocument(src).promise;
        if (dead) return void doc.destroy();
        setPdf(doc);
      } catch {
        if (!dead) setError(true);
      }
    })();
    return () => {
      dead = true;
      void doc?.destroy();
    };
  }, [src, isPdf]);

  return (
    <div ref={box} className="space-y-3">
      {error ? <p className="text-sm text-fail">The source document could not be shown.</p> : null}
      {!isPdf ? (
        <Frame n={1} size={null} highlight={highlight} image>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={src} alt="Source document" className="block h-auto w-full" />
        </Frame>
      ) : pdf ? (
        Array.from({ length: pdf.numPages }, (_, i) => <PdfPage key={i} pdf={pdf} n={i + 1} width={width} highlight={highlight} />)
      ) : !error ? (
        <p className="text-sm text-ink-2" role="status">Loading the document…</p>
      ) : null}
    </div>
  );
}
