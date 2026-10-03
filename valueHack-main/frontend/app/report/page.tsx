"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Download, Loader2, FileText, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { compareActions, getReportPdf, ApiError } from "@/lib/api";
import type { ActionsCompareResponse } from "@/lib/types";
import { formatCount, formatDay, formatInr } from "@/lib/format";
import { EstimateBadge, RiskBadge } from "@/components/ui/badges";
import { ErrorState, LoadingSkeleton } from "@/components/ui/states";
import { GlassCard } from "@/components/ui/GlassCard";

export default function Report() {
  const [delay, setDelay] = useState(14);
  const [actions, setActions] = useState<ActionsCompareResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [pdfState, setPdfState] = useState<"idle" | "busy" | "done" | "fail">("idle");

  const load = useCallback(async (d: number) => {
    setLoading(true);
    setError(null);
    try {
      setActions(await compareActions(d));
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(delay);
  }, [delay, load]);

  const doNothing = actions?.do_nothing;
  const suggested = actions ? Object.values(actions).find((a) => a.suggested) : undefined;

  const downloadPdf = async () => {
    setPdfState("busy");
    const toastId = toast.loading("Generating 1-page PDF decision document...");
    try {
      const blob = await getReportPdf();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "bizsim-decision-report.pdf";
      a.click();
      URL.revokeObjectURL(url);
      setPdfState("done");
      toast.success("PDF Downloaded!", {
        id: toastId,
        description: "Downloaded bizsim-decision-report.pdf cleanly.",
      });
    } catch {
      setPdfState("fail");
      toast.error("PDF Generation Failed", {
        id: toastId,
        description: "Could not fetch report PDF from /api/report.",
      });
    }
  };

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
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">Decision Report</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Executive summary and strategy evaluation for business owners and stakeholders.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <EstimateBadge />
          <button
            onClick={downloadPdf}
            disabled={pdfState === "busy"}
            className="flex items-center gap-2 rounded-2xl bg-primary px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-primary/25 hover:bg-primary/90 transition-all disabled:opacity-50"
          >
            {pdfState === "busy" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            Download Executive PDF
          </button>
        </div>
      </div>

      {/* Delay Slider Control */}
      <GlassCard className="p-6 space-y-2">
        <div className="flex items-center justify-between">
          <label htmlFor="report-delay" className="text-xs font-semibold text-muted-foreground">
            Disruption Scenario: Supplier A Delay Duration
          </label>
          <span className="font-mono text-sm font-bold text-primary font-tabular">{delay} Days</span>
        </div>
        <input
          id="report-delay"
          type="range"
          min={0}
          max={30}
          value={delay}
          onChange={(e) => setDelay(Number(e.target.value))}
          className="w-full accent-primary h-2 bg-muted rounded-lg cursor-pointer"
        />
      </GlassCard>

      {/* A4 Paper-Style Document Preview Card */}
      <div className="rounded-3xl border border-card-border bg-card p-8 sm:p-12 shadow-2xl space-y-8 text-foreground">
        {/* Document Header */}
        <div className="flex items-center justify-between border-b border-card-border pb-6">
          <div>
            <div className="flex items-center gap-2">
              <FileText className="w-6 h-6 text-primary" />
              <h2 className="text-2xl font-black text-foreground">BizSim Executive Brief</h2>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Business: <strong>Sharma Hardware and Electricals</strong> · Scenario: Supplier A is {delay} days late
            </p>
          </div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground border border-card-border bg-muted/40 px-3 py-1 rounded-full">
            Confidential Brief
          </span>
        </div>

        {error ? (
          <ErrorState error={error} title="Could not build the report" onRetry={() => load(delay)} />
        ) : loading && !actions ? (
          <LoadingSkeleton rows={5} className="h-32" />
        ) : (
          doNothing && (
            <div className="space-y-8">
              {/* Section 1: If Nothing Is Done */}
              <div className="space-y-3">
                <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" /> 1. Baseline Risk (&quot;If Nothing Is Done&quot;)
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3.5 rounded-xl border border-card-border bg-muted/40 font-mono font-tabular">
                    <span className="text-muted-foreground block text-[10px] uppercase font-bold">Stock-out Date</span>
                    <span className="text-foreground font-bold">{formatDay(doNothing.summary?.stockout_day)}</span>
                  </div>
                  <div className="p-3.5 rounded-xl border border-card-border bg-muted/40 font-mono font-tabular">
                    <span className="text-muted-foreground block text-[10px] uppercase font-bold">First Negative Cash Day</span>
                    <span className="text-red-500 font-bold">{formatDay(doNothing.summary?.first_negative_day)}</span>
                  </div>
                  <div className="p-3.5 rounded-xl border border-card-border bg-muted/40 font-mono font-tabular">
                    <span className="text-muted-foreground block text-[10px] uppercase font-bold">Lowest Cash Balance</span>
                    <span className="text-red-500 font-bold">{formatInr(doNothing.summary?.lowest_cash_inr)}</span>
                  </div>
                  <div className="p-3.5 rounded-xl border border-card-border bg-muted/40 font-mono font-tabular">
                    <span className="text-muted-foreground block text-[10px] uppercase font-bold">Failed Supplier Payments</span>
                    <span className="text-foreground font-bold">{formatCount(doNothing.summary?.failed_payments_count)}</span>
                  </div>
                </div>
              </div>

              {/* Section 2: Engine Recommendation */}
              <div className="space-y-3">
                <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-green-500" /> 2. Recommended Engine Strategy
                </h3>
                {suggested ? (
                  <div className="rounded-2xl border border-green-500/30 bg-green-500/10 p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-sm text-foreground">{suggested.label}</h4>
                      <RiskBadge level={suggested.risk.level} />
                    </div>
                    <p className="text-xs text-foreground leading-relaxed">{suggested.suggested_reason}</p>
                    <p className="font-mono text-xs font-bold text-green-500 font-tabular">
                      Lowest cash: {formatInr(suggested.summary?.lowest_cash_inr)} · 30-Day end cash: {formatInr(suggested.summary?.end_cash_inr)}
                    </p>
                  </div>
                ) : (
                  <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5 text-xs text-amber-500">
                    No action completely avoids the cash gap for this scenario. {Object.values(actions ?? {})[0]?.suggested_reason}
                  </div>
                )}
              </div>

              {/* Section 3: Action Comparison Table */}
              <div className="space-y-3">
                <h3 className="text-base font-bold text-foreground">3. Mitigation Actions Matrix</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="border-b border-card-border bg-muted/40 text-muted-foreground font-bold uppercase tracking-wider">
                      <tr>
                        <th className="p-3">Option</th>
                        <th className="p-3">Risk Level</th>
                        <th className="p-3 text-right">Lowest Cash</th>
                        <th className="p-3 text-right">End Cash</th>
                        <th className="p-3 text-right">Failed Payments</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-card-border font-mono font-tabular">
                      {Object.entries(actions).map(([key, act]) => (
                        <tr key={key} className={act.suggested ? "bg-primary/10 font-bold" : ""}>
                          <td className="p-3 font-sans text-foreground">
                            {act.label} {act.suggested && <span className="text-[10px] text-primary uppercase font-bold ml-1">(Suggested)</span>}
                          </td>
                          <td className="p-3">
                            <RiskBadge level={act.risk.level} />
                          </td>
                          <td className="p-3 text-right text-foreground">{formatInr(act.summary?.lowest_cash_inr)}</td>
                          <td className="p-3 text-right text-foreground">{formatInr(act.summary?.end_cash_inr)}</td>
                          <td className="p-3 text-right text-foreground">{act.summary?.failed_payments_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )
        )}
      </div>
    </motion.div>
  );
}
