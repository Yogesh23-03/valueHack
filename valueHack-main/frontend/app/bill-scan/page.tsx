"use client";

import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Loader2, UploadCloud, AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, FileText, DollarSign, Zap } from "lucide-react";
import { scanBill } from "@/lib/api";
import { formatInr } from "@/lib/format";
import { ErrorState } from "@/components/ui/states";
import { GlassCard } from "@/components/ui/GlassCard";

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
  green: "text-green-500 bg-green-500/10 border-green-500/30",
  amber: "text-amber-500 bg-amber-500/10 border-amber-500/30",
  red: "text-red-500 bg-red-500/10 border-red-500/30",
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
    const toastId = toast.loading("Scanning document for overcharges and tax flags...");

    try {
      const res = await scanBill(file);
      setResult(res);
      toast.success("Bill Audited Successfully!", {
        id: toastId,
        description: `Found ${res.flag_count} discrepancy flag(s) on ${res.supplier} invoice.`,
      });
    } catch (e) {
      setError(e);
      toast.error("Scanning Error", {
        id: toastId,
        description: "Failed to audit the invoice document.",
      });
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
      toast.success("Payable Recorded!", {
        description: `Added ${formatInr(result.total_amount)} payable for ${result.supplier} into database.`,
      });
    } catch {
      toast.error("Could not record payable");
    } finally {
      setConfirming(false);
    }
  };

  const vendorBadge = result?.vendor_risk?.badge as keyof typeof BADGE_COLORS | undefined;

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mx-auto max-w-4xl space-y-8"
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-card-border pb-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">Bill Scanner & Overcharge Audit</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Scan supplier invoices for &gt;10% price spikes vs history, HSN tax mismatches, and automated payable entry.
          </p>
        </div>
      </div>

      {/* Dropzone with Scan Line animation */}
      <div className="relative overflow-hidden">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={busy}
          className="w-full glass-card p-10 flex flex-col items-center justify-center border-2 border-dashed border-card-border hover:border-primary/50 transition-all group cursor-pointer"
        >
          {busy ? (
            <Loader2 className="mb-3 h-10 w-10 animate-spin text-primary" />
          ) : (
            <UploadCloud className="mb-3 h-10 w-10 text-muted-foreground group-hover:text-primary transition-colors" />
          )}
          <span className="text-sm font-bold text-foreground">
            {busy ? "Auditing Document with Vision Model..." : "Upload Invoice (PDF / Image / Text)"}
          </span>
          <span className="text-xs text-muted-foreground mt-1">Click to browse or drop file here</span>

          {/* Sweeping Scan Line when busy */}
          {busy && (
            <motion.div
              animate={{ y: [0, 100, 0] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
              className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-primary to-transparent shadow-[0_0_15px_#8B5CF6]"
            />
          )}
        </button>

        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.txt"
          onChange={(e) => handleFile(e.target.files?.[0])}
          className="hidden"
        />
      </div>

      {/* Preset Bill Samples */}
      <div className="flex flex-wrap items-center justify-center gap-2">
        <span className="text-xs text-muted-foreground font-medium mr-1">Sample Invoices:</span>
        {SAMPLE_LABELS.map((item) => (
          <button
            key={item.filename}
            onClick={() => {
              const file = new File([item.filename], item.filename, { type: "text/plain" });
              handleFile(file);
            }}
            className="text-xs font-semibold px-3 py-1.5 rounded-full border border-card-border bg-card/60 hover:bg-muted text-muted-foreground hover:text-foreground transition-all"
          >
            {item.label}
          </button>
        ))}
      </div>

      {error ? <ErrorState error={error} title="Could not audit the invoice" onRetry={() => inputRef.current?.click()} /> : null}

      {/* Audited Result Card */}
      {result && (
        <GlassCard className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-card-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                <h2 className="text-xl font-bold text-foreground">{result.supplier}</h2>
              </div>
              <p className="text-xs text-muted-foreground font-mono font-tabular mt-0.5">
                Invoice #{result.invoice_number} · GSTIN: {result.supplier_gstin} · Date: {result.invoice_date}
              </p>
            </div>

            {vendorBadge && (
              <span className={`px-3 py-1 rounded-full border text-xs font-bold capitalize ${BADGE_COLORS[vendorBadge]}`}>
                Vendor Score: {result.vendor_risk.score}/100 ({result.vendor_risk.risk_level} Risk)
              </span>
            )}
          </div>

          {/* Line Items Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-card-border bg-muted/40 text-muted-foreground font-bold uppercase tracking-wider">
                <tr>
                  <th className="p-3">Item Description</th>
                  <th className="p-3">HSN</th>
                  <th className="p-3 text-right">Qty</th>
                  <th className="p-3 text-right">Unit Price</th>
                  <th className="p-3 text-right">Tax Rate</th>
                  <th className="p-3 text-right">Flags</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-card-border font-mono font-tabular">
                {result.items.map((item, idx) => (
                  <tr key={idx} className={item.has_overcharge ? "bg-red-500/10" : "hover:bg-muted/30"}>
                    <td className="p-3 font-sans font-bold text-foreground">{item.name}</td>
                    <td className="p-3 text-muted-foreground">{item.hsn_code ?? "N/A"}</td>
                    <td className="p-3 text-right text-foreground">{item.qty}</td>
                    <td className="p-3 text-right text-foreground">{formatInr(item.unit_price)}</td>
                    <td className="p-3 text-right text-foreground">{item.tax_rate}%</td>
                    <td className="p-3 text-right">
                      {item.has_overcharge ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/20 text-red-500 border border-red-500/30 text-[10px] font-bold">
                          <AlertTriangle className="w-3 h-3" /> Overcharge Flag
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/20 text-green-500 border border-green-500/30 text-[10px] font-bold">
                          <CheckCircle2 className="w-3 h-3" /> OK
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Summary Bar & Payable Confirmation Button */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-card-border">
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Total Payable Amount:</p>
              <p className="font-mono text-2xl font-bold text-foreground font-tabular">{formatInr(result.total_amount)}</p>
              <span className="text-[11px] font-bold text-warning">{result.flag_count} Discrepancy Flag(s) Detected</span>
            </div>

            <button
              onClick={handleConfirmPayable}
              disabled={confirming || confirmed}
              className="px-8 py-3.5 rounded-2xl bg-primary text-white font-bold text-xs shadow-lg shadow-primary/25 hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {confirming ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : confirmed ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-green-400" /> Payable Recorded
                </>
              ) : (
                <>
                  <DollarSign className="w-4 h-4" /> Confirm & Add to Payables
                </>
              )}
            </button>
          </div>
        </GlassCard>
      )}
    </motion.div>
  );
}
