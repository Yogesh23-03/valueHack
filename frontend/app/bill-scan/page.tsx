"use client";

import { useRef, useState } from "react";
import { Loader2, UploadCloud, AlertTriangle, CheckCircle, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import { scanBill } from "@/lib/api";
import { formatInr } from "@/lib/format";
import { ErrorState } from "@/components/ui/states";

interface BillFlag {
  type: string;
  severity: string;
  item: string;
  message: string;
  expected_price?: number;
  actual_price?: number;
  excess_amount_inr?: number;
  expected_tax?: number;
  actual_tax?: number;
}

interface BillItem {
  name: string;
  hsn_code?: string;
  qty: number;
  unit_price: number;
  tax_rate: number;
  flags: BillFlag[];
  has_overcharge: boolean;
}

interface VendorRisk {
  score: number;
  badge: string;
  risk_level: string;
  reasons: string[];
}

interface BillResult {
  invoice_number: string;
  supplier: string;
  supplier_gstin: string;
  invoice_date: string;
  due_date: string;
  items: BillItem[];
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  flags: BillFlag[];
  flag_count: number;
  vendor_risk: VendorRisk;
  is_payable_ready: boolean;
}

const BADGE_COLORS = {
  green: 'text-green-400 bg-green-500/10 border-green-500/30',
  amber: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  red: 'text-red-400 bg-red-500/10 border-red-500/30',
};

const SAMPLE_LABELS = [
  { label: "Standard Invoice", filename: "sample_bill_1_supplier_a_standard.txt" },
  { label: "Overpriced Fans (+20%)", filename: "sample_bill_2_overpriced_fans.txt" },
  { label: "Tax Rate Mismatch", filename: "sample_bill_3_tax_mismatch.txt" },
  { label: "New Distributor", filename: "sample_bill_4_new_distributor.txt" },
];

export default function BillScan() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<BillResult | null>(null);
  const [showAllFlags, setShowAllFlags] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    setBusy(true);
    setError(null);
    setResult(null);
    setConfirmed(false);
    try {
      setResult(await scanBill(file));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  const handleConfirmPayable = async () => {
    if (!result) return;
    setConfirming(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      await fetch(`${apiBase}/api/bill/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          supplier: result.supplier,
          amount: result.total_amount,
          due_day: 25,
          invoice_number: result.invoice_number,
        }),
      });
      setConfirmed(true);
    } catch {
      /* ignore */
    } finally {
      setConfirming(false);
    }
  };

  const vendorBadge = result?.vendor_risk?.badge as keyof typeof BADGE_COLORS | undefined;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold">Bill Scan</h1>
        <p className="mt-2 text-sm text-zinc-400">
          Upload a supplier invoice. The engine flags overcharges (&gt;10% above history) and HSN tax rate mismatches.
        </p>
      </div>

      {/* Upload zone */}
      <button
        type="button"
        id="bill-upload-btn"
        onClick={() => inputRef.current?.click()}
        disabled={busy}
        className="glass group mx-auto flex w-full max-w-2xl cursor-pointer flex-col items-center rounded-3xl border-2 border-dashed border-white/20 p-12 transition-colors hover:border-primary/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
      >
        {busy ? (
          <Loader2 className="mb-3 h-10 w-10 animate-spin text-primary" />
        ) : (
          <UploadCloud className="mb-3 h-10 w-10 text-zinc-400 transition-colors group-hover:text-primary" />
        )}
        <span className="text-lg font-medium">{busy ? "Scanning…" : "Upload an invoice (PDF / image / text)"}</span>
        <span className="mt-1 text-sm text-zinc-500">or click to browse</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt,image/*"
        className="hidden"
        aria-label="Invoice file"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />

      {/* Sample quick-loads */}
      <div>
        <p className="text-xs text-center text-zinc-500 mb-2">Quick demo samples:</p>
        <div className="flex flex-wrap justify-center gap-2">
          {SAMPLE_LABELS.map((s) => (
            <button
              key={s.filename}
              className="text-xs px-3 py-1.5 rounded-full glass border border-white/10 hover:border-primary/50 transition"
              onClick={() => {
                const text = `sample:${s.filename}`;
                const blob = new Blob([text], { type: "text/plain" });
                handleFile(new File([blob], s.filename, { type: "text/plain" }));
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <ErrorState error={error} title="The scan could not run" onRetry={() => setError(null)} />
      ) : null}

      {/* Result */}
      {result && (
        <div className="glass mx-auto max-w-2xl rounded-3xl overflow-hidden border border-white/10 space-y-0">
          {/* Flag summary banner */}
          {result.flag_count > 0 && (
            <div className="bg-red-500/10 border-b border-red-500/20 px-6 py-3 flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
              <span className="text-sm font-medium text-red-300">
                {result.flag_count} flag{result.flag_count > 1 ? 's' : ''} detected — review before confirming payable
              </span>
            </div>
          )}

          {/* Invoice header */}
          <div className="px-6 pt-5 pb-4 border-b border-white/8">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold">{result.supplier}</h2>
                {result.supplier_gstin && (
                  <p className="text-xs text-zinc-500 mt-0.5">GSTIN: {result.supplier_gstin}</p>
                )}
                <p className="text-xs text-zinc-400 mt-1">
                  Invoice #{result.invoice_number} &bull; Date: {result.invoice_date} &bull; Due: {result.due_date}
                </p>
              </div>
              {/* Vendor risk badge */}
              {result.vendor_risk && vendorBadge && (
                <div className={`text-xs font-bold px-3 py-1.5 rounded-full border uppercase ${BADGE_COLORS[vendorBadge]}`}>
                  Vendor: {result.vendor_risk.risk_level} Risk ({result.vendor_risk.score})
                </div>
              )}
            </div>
          </div>

          {/* Line items */}
          <div className="px-6 py-4 space-y-2">
            {result.items.map((item, i) => (
              <div key={i} className={`rounded-xl p-3 text-sm ${item.has_overcharge ? 'bg-red-500/5 border border-red-500/20' : 'bg-white/5'}`}>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {item.has_overcharge
                      ? <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                      : <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                    }
                    <span className="font-medium truncate">{item.name}</span>
                    {item.hsn_code && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-zinc-500 shrink-0">
                        HSN {item.hsn_code}
                      </span>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <div className="font-mono text-zinc-200">{formatInr(item.unit_price)} × {item.qty}</div>
                    <div className="text-[11px] text-zinc-500">{item.tax_rate}% GST</div>
                  </div>
                </div>
                {/* Item flags */}
                {item.flags.map((f, fi) => (
                  <div key={fi} className="mt-2 text-xs text-red-300 flex items-start gap-2 pl-6">
                    <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0 text-red-400" />
                    {f.message}
                  </div>
                ))}
              </div>
            ))}
          </div>

          {/* Totals */}
          <div className="px-6 py-3 bg-white/[0.02] border-t border-white/8 text-sm flex flex-col items-end gap-1">
            <div className="text-zinc-400">Subtotal: <span className="text-white font-mono">{formatInr(result.subtotal)}</span></div>
            <div className="text-zinc-400">GST: <span className="text-white font-mono">{formatInr(result.tax_amount)}</span></div>
            <div className="text-lg font-bold">Total: <span className="font-mono">{formatInr(result.total_amount)}</span></div>
          </div>

          {/* All flags collapsible */}
          {result.flag_count > 0 && (
            <div className="px-6 pb-4">
              <button
                onClick={() => setShowAllFlags(!showAllFlags)}
                className="flex items-center gap-2 text-xs text-zinc-400 hover:text-white transition mt-2"
              >
                {showAllFlags ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {showAllFlags ? 'Hide' : 'Show all'} flags ({result.flag_count})
              </button>
              {showAllFlags && (
                <div className="mt-3 space-y-2">
                  {result.flags.map((f, fi) => (
                    <div key={fi} className="rounded-xl p-3 bg-red-500/5 border border-red-500/20 text-xs text-red-300">
                      <span className="font-semibold uppercase text-red-400 mr-2">{f.type.replace('_', ' ')}</span>
                      {f.message}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Confirm payable */}
          <div className="px-6 pb-6">
            {confirmed ? (
              <div className="flex items-center gap-2 justify-center py-3 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium">
                <CheckCircle className="w-4 h-4" /> Payable added to your records
              </div>
            ) : (
              <button
                id="confirm-payable-btn"
                onClick={handleConfirmPayable}
                disabled={confirming}
                className="w-full py-3 rounded-xl bg-primary/90 hover:bg-primary text-white text-sm font-semibold transition disabled:opacity-50"
              >
                {confirming ? 'Adding…' : `Confirm & Add Payable (${formatInr(result.total_amount)})`}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
