import type { Ranges } from "@/lib/types";
import { formatCount, formatDay, formatInr } from "@/lib/format";
import { EstimateBadge } from "@/components/ui/badges";

/**
 * Demand ranges: min / base / max per metric from `ranges.metrics`, plus the
 * engine's own `range_note` sentence. The engine returns metric summaries
 * (no per-day low/high timelines), so no shaded band is drawn — that would
 * require the frontend to compute business figures.
 */

const ROWS: Array<{ key: string; label: string; unit: string }> = [
  { key: "stockout_day", label: "First stock-out day", unit: "day" },
  { key: "lost_sales_inr", label: "Lost walk-in sales", unit: "inr" },
  { key: "first_negative_day", label: "First day cash is below zero", unit: "day" },
  { key: "lowest_cash_inr", label: "Lowest cash", unit: "inr" },
  { key: "end_cash_inr", label: "End cash", unit: "inr" },
];

function fmt(unit: string, v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  if (unit === "inr") return formatInr(v);
  if (unit === "day") return formatDay(v);
  return formatCount(v);
}

export default function RangesPanel({ ranges }: { ranges: Ranges | undefined }) {
  if (!ranges) return null;
  return (
    <section aria-label="Demand ranges">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
          If demand is higher or lower
        </h3>
        <EstimateBadge />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[420px] text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-zinc-500">
              <th className="py-2 pr-4 font-medium">Metric</th>
              <th className="py-2 pr-4 font-medium">Low demand</th>
              <th className="py-2 pr-4 font-medium">Base</th>
              <th className="py-2 font-medium">High demand</th>
            </tr>
          </thead>
          <tbody className="font-mono">
            {ROWS.filter((r) => ranges.metrics[r.key]).map((r) => {
              const m = ranges.metrics[r.key];
              return (
                <tr key={r.key} className="border-t border-white/5">
                  <td className="py-2 pr-4 font-sans text-zinc-300">{r.label}</td>
                  <td className="py-2 pr-4 text-zinc-400">{fmt(r.unit, m.min)}</td>
                  <td className="py-2 pr-4 text-zinc-100">{fmt(r.unit, m.base)}</td>
                  <td className="py-2 text-zinc-400">{fmt(r.unit, m.max)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {ranges.range_note && (
        <p className="mt-3 rounded-xl border border-white/5 bg-white/5 p-3 text-sm text-zinc-300">
          <span className="font-semibold text-primary">Range note: </span>
          {ranges.range_note}
        </p>
      )}
    </section>
  );
}
