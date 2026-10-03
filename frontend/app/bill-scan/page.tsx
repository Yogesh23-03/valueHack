"use client";

import { useRef, useState } from "react";
import { Loader2, UploadCloud } from "lucide-react";
import { scanBill } from "@/lib/api";
import type { BillScanResult } from "@/lib/types";
import { formatInr } from "@/lib/format";
import { ErrorState } from "@/components/ui/states";

/**
 * Bill scan. The backend endpoint /api/bill/scan is currently a stub that
 * returns a fixed sample — no file parsing happens. The UI calls it anyway
 * and labels the output honestly as demo stub output.
 */
export default function BillScan() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<BillScanResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await scanBill(file));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-8 text-center">
      <div>
        <h1 className="text-3xl font-bold">Bill scan</h1>
        <p className="mt-2 text-sm text-zinc-400">
          Upload a supplier invoice. <span className="text-amber-400">Demo stub:</span> the endpoint currently returns a
          fixed sample response — no real extraction yet.
        </p>
      </div>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={busy}
        className="glass group mx-auto flex w-full max-w-2xl cursor-pointer flex-col items-center rounded-3xl border-2 border-dashed border-white/20 p-16 transition-colors hover:border-primary/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
      >
        {busy ? (
          <Loader2 className="mb-3 h-10 w-10 animate-spin text-primary" aria-hidden />
        ) : (
          <UploadCloud className="mb-3 h-10 w-10 text-zinc-400 transition-colors group-hover:text-primary" aria-hidden />
        )}
        <span className="text-lg font-medium">{busy ? "Scanning…" : "Upload an invoice (PDF/image)"}</span>
        <span className="mt-1 text-sm text-zinc-500">or click to browse</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,image/*"
        className="hidden"
        aria-label="Invoice file"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />

      {error ? <ErrorState error={error} title="The scan could not run" onRetry={() => setError(null)} /> : null}

      {result && (
        <div className="glass mx-auto max-w-2xl rounded-3xl p-8 text-left">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-bold">{result.supplier}</h2>
            <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-400">
              demo stub output
            </span>
          </div>
          <p className="text-sm text-zinc-400">Due {result.due_date}</p>
          <ul className="mt-3 space-y-2">
            {result.items.map((it, i) => (
              <li key={i} className="flex items-center justify-between rounded-xl bg-white/5 p-3 text-sm">
                <span>
                  {it.name} × {it.qty}
                </span>
                <span className="font-mono text-zinc-300">
                  {formatInr(it.unit_price)} · {it.tax_rate}% tax
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
