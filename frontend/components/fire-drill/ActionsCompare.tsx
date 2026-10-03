"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, ExternalLink, Lightbulb } from "lucide-react";
import type { ActionCompareResult, ActionsCompareResponse } from "@/lib/types";
import { formatCount, formatDay, formatInr } from "@/lib/format";
import { RiskBadge } from "@/components/ui/badges";
import { ErrorState, EmptyState } from "@/components/ui/states";

/**
 * Action comparison cards. Every number, sentence, factor and flag comes
 * straight from POST /api/actions/compare — the UI only formats and lays out.
 */

function signedDelta(key: string, delta: number | undefined): string {
  if (delta === undefined || delta === null) return "—";
  if (key.endsWith("_day")) return `${delta > 0 ? "+" : ""}${delta} d`;
  return `${delta > 0 ? "+" : ""}${formatInr(delta)}`;
}

function Metric({ label, value, delta }: { label: string; value: string; delta?: string }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="font-mono text-sm text-zinc-100">
        {value}
        {delta && delta !== "—" && <span className="ml-1 text-[10px] text-zinc-500">({delta} vs do nothing)</span>}
      </p>
    </div>
  );
}

function ActionCard({ id, res }: { id: string; res: ActionCompareResult }) {
  const [showVendorFails, setShowVendorFails] = useState(false);
  const s = res.summary;
  const isSwitch = id === "switch_supplier";

  return (
    <div
      className={`rounded-2xl border p-4 ${
        res.suggested ? "border-green-500/40 bg-green-500/5" : "border-white/5 bg-white/5"
      }`}
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-sm font-bold text-zinc-100">{res.label}</h4>
        <div className="flex flex-wrap items-center gap-1.5">
          {res.suggested && (
            <span className="inline-flex items-center gap-1 rounded-full border border-green-500/40 bg-green-500/15 px-2 py-0.5 text-[10px] font-bold uppercase text-green-400">
              <Lightbulb className="h-3 w-3" aria-hidden /> Engine suggests
            </span>
          )}
          <RiskBadge level={res.risk.level} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Metric label="Stock-out" value={formatDay(s?.stockout_day)} delta={signedDelta("stockout_day", res.delta_vs_do_nothing?.stockout_day?.delta)} />
        <Metric label="Lowest cash" value={formatInr(s?.lowest_cash_inr)} delta={signedDelta("lowest_cash_inr", res.delta_vs_do_nothing?.lowest_cash_inr?.delta)} />
        <Metric label="End cash" value={formatInr(s?.end_cash_inr)} delta={signedDelta("end_cash_inr", res.delta_vs_do_nothing?.end_cash_inr?.delta)} />
        <Metric label="Failed payments" value={formatCount(s?.failed_payments_count)} />
      </div>

      {res.tradeoff && <p className="mt-3 text-xs leading-snug text-zinc-400">{res.tradeoff}</p>}

      <div className="mt-3 flex flex-wrap gap-1.5">
        {res.affordable ? (
          <span className="rounded-full border border-green-500/30 bg-green-500/10 px-2 py-0.5 text-[10px] font-semibold text-green-400">
            Affordable on the day
          </span>
        ) : (
          <span className="rounded-full border border-red-500/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-semibold text-red-400">
            Not affordable — shortfall {formatInr(res.shortfall_inr)}
          </span>
        )}
        {res.requires_counterparty_agreement && (
          <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-400">
            Needs the other party to agree
          </span>
        )}
      </div>

      {/* Expandable: risk factors + demand range for this action */}
      <details className="mt-3">
        <summary className="flex cursor-pointer items-center gap-1 text-xs font-medium text-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
          <ChevronDown className="h-3.5 w-3.5" aria-hidden /> Risk factors &amp; range
        </summary>
        <ul className="mt-2 space-y-1.5">
          {res.risk.factors.map((f, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-zinc-300">
              <span className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[10px] text-zinc-400">+{f.points}</span>
              {f.reason}
            </li>
          ))}
        </ul>
        {res.ranges?.metrics?.end_cash_inr && (
          <p className="mt-2 text-xs text-zinc-400">
            Across the demand range, end cash goes from {formatInr(res.ranges.metrics.end_cash_inr.min)} to{" "}
            {formatInr(res.ranges.metrics.end_cash_inr.max)}.
          </p>
        )}
        {res.ranges?.range_note && <p className="mt-1 text-xs text-zinc-500">{res.ranges.range_note}</p>}
      </details>

      {/* switch_supplier extras: vendor risk + vendor vanishes */}
      {isSwitch && res.vendor_risk && (
        <div className="mt-3 rounded-xl border border-white/10 bg-black/20 p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase ${
                res.vendor_risk.band === "red"
                  ? "border-red-500/30 bg-red-500/10 text-red-400"
                  : res.vendor_risk.band === "amber"
                    ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                    : res.vendor_risk.band === "green"
                      ? "border-green-500/30 bg-green-500/10 text-green-400"
                      : "border-white/10 bg-white/5 text-zinc-400"
              }`}
            >
              {res.vendor_risk.band} vendor
            </span>
            <span className="text-xs text-zinc-400">
              Trust score {res.vendor_risk.score < 0 ? "unknown (mock check not connected)" : res.vendor_risk.score}
            </span>
          </div>
          <ul className="mt-1.5 list-disc space-y-0.5 pl-4 text-[11px] text-zinc-400">
            {res.vendor_risk.reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
          {res.exposure_inr != null && (
            <p className="mt-1.5 text-xs text-amber-400">
              Money at risk with this vendor: {formatInr(res.exposure_inr)} (mock estimate)
            </p>
          )}
          {res.vendor_fails_result && (
            <div className="mt-2">
              <button
                onClick={() => setShowVendorFails((v) => !v)}
                aria-expanded={showVendorFails}
                className="rounded-lg border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-xs font-medium text-red-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
              >
                {showVendorFails ? "Hide" : "Show"} if the vendor vanishes
              </button>
              {showVendorFails && (
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                  <Metric label="Lowest cash" value={formatInr(res.vendor_fails_result.summary?.lowest_cash_inr ?? res.vendor_fails_result.min_cash)} />
                  <Metric label="First day below zero" value={formatDay(res.vendor_fails_result.summary?.first_negative_day ?? res.vendor_fails_result.first_negative_day)} />
                  <Metric label="End cash" value={formatInr(res.vendor_fails_result.summary?.end_cash_inr ?? res.vendor_fails_result.end_cash)} />
                  <Metric label="Failed payments" value={formatCount(res.vendor_fails_result.summary?.failed_payments_count ?? res.vendor_fails_result.failed?.length)} />
                </div>
              )}
            </div>
          )}
          <Link
            href="/vendor-check"
            className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
          >
            Check this vendor on the Vendor Check screen <ExternalLink className="h-3 w-3" aria-hidden />
          </Link>
        </div>
      )}
    </div>
  );
}

export default function ActionsCompare({
  actions,
  error,
  onRetry,
  scenarioNote,
}: {
  actions: ActionsCompareResponse | null;
  error: unknown;
  onRetry: () => void;
  scenarioNote: string | null;
}) {
  if (error) return <ErrorState error={error} title="Could not compare actions" onRetry={onRetry} />;
  if (!actions) {
    return (
      <EmptyState
        title="No action comparison yet"
        hint={scenarioNote ?? "Run a supplier delay to compare what you could do about it."}
      />
    );
  }

  const suggested = Object.values(actions).find((a) => a.suggested);

  return (
    <section aria-label="Action comparison">
      <h3 className="mb-1 text-sm font-semibold uppercase tracking-wider text-zinc-400">What could you do?</h3>
      <p className="mb-3 text-xs text-zinc-500">
        {scenarioNote ?? "Compared for the scenario above."} The tool suggests; the owner decides.
      </p>
      {suggested ? (
        <p className="mb-3 rounded-xl border border-green-500/20 bg-green-500/5 p-3 text-sm text-green-300">
          <span className="font-semibold">Engine suggestion: </span>
          {suggested.suggested_reason}
        </p>
      ) : (
        Object.values(actions)[0]?.suggested_reason && (
          <p className="mb-3 rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 text-sm text-amber-300">
            <span className="font-semibold">No action suggested. </span>
            {Object.values(actions)[0].suggested_reason}
          </p>
        )
      )}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {Object.entries(actions).map(([id, res]) => (
          <ActionCard key={id} id={id} res={res} />
        ))}
      </div>
    </section>
  );
}
