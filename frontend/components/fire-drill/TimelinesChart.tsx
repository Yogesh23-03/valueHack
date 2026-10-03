"use client";

import { useMemo } from "react";
import {
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CascadeResult, FailedPayment } from "@/lib/types";
import { formatInr } from "@/lib/format";

/**
 * Cash and stock timelines drawn from API arrays only. Markers:
 * first negative day, failed payment days, the selected cascade step day,
 * and days of events highlighted from the "Why?" panel.
 */

const tooltipStyle = {
  backgroundColor: "#12121A",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  fontSize: 12,
};

function inrTooltipFormatter(value: unknown) {
  return typeof value === "number" ? formatInr(value) : String(value ?? "");
}

export default function TimelinesChart({
  result,
  baseline,
  actionTimeline,
  actionLabel,
  selectedDay,
  highlightEventDays,
}: {
  result: CascadeResult;
  baseline?: number[] | null;
  actionTimeline?: number[] | null;
  actionLabel?: string;
  selectedDay: number | null;
  highlightEventDays: number[];
}) {
  const cashData = useMemo(
    () =>
      result.cash_timeline.map((v, i) => ({
        day: i + 1,
        cash: v,
        baseline: baseline?.[i] ?? null,
        action: actionTimeline?.[i] ?? null,
      })),
    [result.cash_timeline, baseline, actionTimeline],
  );

  const products = useMemo(
    () => (result.stock_timeline.length ? Object.keys(result.stock_timeline[0]) : []),
    [result.stock_timeline],
  );
  const stockData = useMemo(
    () => result.stock_timeline.map((p, i) => ({ day: i + 1, ...p })),
    [result.stock_timeline],
  );

  const failedDots = (result.failed ?? []).map((f: FailedPayment) => ({
    day: f.day,
    y: result.cash_timeline[f.day - 1],
    name: f.name,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-zinc-400">
          Cash runway <span className="normal-case text-zinc-600">(rupees by day)</span>
        </h3>
        <div className="h-56" role="img" aria-label="Cash by day line chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={cashData} margin={{ top: 12, right: 16, left: 4, bottom: 0 }}>
              <XAxis dataKey="day" stroke="#A1A1AA" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis
                stroke="#A1A1AA"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `₹${Math.round(Number(v) / 1000)}k`}
              />
              <Tooltip contentStyle={tooltipStyle} formatter={inrTooltipFormatter} />
              <ReferenceLine y={0} stroke="#EF4444" strokeDasharray="4 4" />
              {result.first_negative_day !== null && (
                <ReferenceLine
                  x={result.first_negative_day}
                  stroke="#EF4444"
                  strokeDasharray="4 4"
                  label={{ value: `cash < 0 (d${result.first_negative_day})`, fill: "#EF4444", fontSize: 10, position: "top" }}
                />
              )}
              {selectedDay !== null && (
                <ReferenceLine x={selectedDay} stroke="#7C5CFF" strokeDasharray="2 3" />
              )}
              {highlightEventDays.map((d) => (
                <ReferenceLine key={`ev-${d}`} x={d} stroke="#F59E0B" strokeDasharray="1 4" />
              ))}
              {baseline && (
                <Line type="monotone" dataKey="baseline" name="No shock (from compare)" stroke="#71717A" strokeWidth={1.5} dot={false} strokeDasharray="5 4" connectNulls />
              )}
              <Line type="monotone" dataKey="cash" name="This scenario" stroke="#EF4444" strokeWidth={2} dot={false} />
              {actionTimeline && (
                <Line type="monotone" dataKey="action" name={actionLabel ?? "Action"} stroke="#22C55E" strokeWidth={2} dot={false} connectNulls />
              )}
              {failedDots.map((f) =>
                f.y !== undefined ? (
                  <ReferenceDot key={f.name} x={f.day} y={f.y} r={5} fill="#EF4444" stroke="#0A0A0F" />
                ) : null,
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-zinc-500">
          <span className="flex items-center gap-1.5"><span className="h-0.5 w-3 rounded bg-zinc-500" aria-hidden /> No shock (from compare)</span>
          <span className="flex items-center gap-1.5"><span className="h-0.5 w-3 rounded bg-red-500" aria-hidden /> This scenario</span>
          {actionTimeline && <span className="flex items-center gap-1.5"><span className="h-0.5 w-3 rounded bg-green-500" aria-hidden /> {actionLabel ?? "Action"}</span>}
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-red-500" aria-hidden /> Failed payment</span>
          <span className="flex items-center gap-1.5"><span className="h-0.5 w-3 rounded bg-amber-500" aria-hidden /> Highlighted event day</span>
        </div>
      </div>

      {products.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-zinc-400">
            Stock on hand <span className="normal-case text-zinc-600">(units by day, per product)</span>
          </h3>
          <div className="h-44" role="img" aria-label="Stock by day line chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stockData} margin={{ top: 8, right: 16, left: 4, bottom: 0 }}>
                <XAxis dataKey="day" stroke="#A1A1AA" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#A1A1AA" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                {result.summary?.stockout_day != null && (
                  <ReferenceLine x={result.summary.stockout_day} stroke="#EF4444" strokeDasharray="4 4"
                    label={{ value: `stock-out d${result.summary.stockout_day}`, fill: "#EF4444", fontSize: 10, position: "top" }} />
                )}
                {products.map((p, i) => (
                  <Line key={p} type="monotone" dataKey={p} name={p} stroke={["#7C5CFF", "#4F9DFF", "#22C55E", "#F59E0B"][i % 4]} strokeWidth={1.8} dot={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
