"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, BarChart3 } from "lucide-react";
import { getBusiness, getAttention } from "@/lib/api";
import type { AttentionItem, BusinessResponse } from "@/lib/types";
import { formatInr } from "@/lib/format";
import { ConcentrationChip, EstimateBadge, StatusChip } from "@/components/ui/badges";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/ui/states";

/**
 * Dashboard: everything from GET /api/business (including the analytics
 * block) plus GET /api/attention. /api/attention is a hard-coded demo stub
 * on the backend (Person 2 scope) — it is labelled "demo reminders" here;
 * the engine's analytics.attention_inputs are shown with their evidence.
 * There is no /api/business/load endpoint, so no CSV upload is faked.
 */

const KIND_SCREEN: Record<string, string> = {
  supplier_concentration: "/fire-drill",
  stock_cover: "/fire-drill",
};

export default function Dashboard() {
  const [business, setBusiness] = useState<BusinessResponse | null>(null);
  const [attention, setAttention] = useState<AttentionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [b, a] = await Promise.all([getBusiness(), getAttention()]);
      setBusiness(b);
      setAttention(a);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (error) {
    return <ErrorState error={error} title="The dashboard could not load" onRetry={load} />;
  }
  if (loading || !business) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton rows={1} className="h-9 w-56" />
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <LoadingSkeleton key={i} rows={1} className="h-24" />
          ))}
        </div>
        <LoadingSkeleton rows={3} className="h-16" />
      </div>
    );
  }

  const dep = business.analytics?.dependency_shares?.supplier_dependency ?? [];
  const cover = business.analytics?.stock_cover ?? [];
  const engineAttention = business.analytics?.attention_inputs ?? [];
  const atRisk = cover.filter((c) => c.status !== "safe").length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{business.name}</h1>
          <p className="text-sm text-zinc-500">Synthetic demo business · estimates, not predictions</p>
        </div>
        <EstimateBadge />
      </div>

      {/* KPIs — every number comes from the API */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="glass rounded-2xl p-5">
          <p className="text-sm font-medium text-zinc-400">Cash on hand</p>
          <p className="mt-2 font-mono text-2xl font-bold">{formatInr(business.cash)}</p>
        </div>
        <div className="glass rounded-2xl p-5">
          <p className="text-sm font-medium text-zinc-400">Products tracked</p>
          <p className="mt-2 font-mono text-2xl font-bold">{cover.length}</p>
        </div>
        <div className="glass rounded-2xl p-5">
          <p className="text-sm font-medium text-zinc-400">Products at risk</p>
          <p className="mt-2 font-mono text-2xl font-bold">{atRisk}</p>
          <p className="text-xs text-zinc-500">watch or critical cover</p>
        </div>
        <div className="glass rounded-2xl p-5">
          <p className="text-sm font-medium text-zinc-400">Suppliers</p>
          <p className="mt-2 font-mono text-2xl font-bold">{dep.length}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Attention lists */}
        <div className="space-y-6 lg:col-span-2">
          <div className="glass rounded-2xl p-6">
            <h2 className="mb-4 text-lg font-semibold">Needs attention (engine analytics)</h2>
            {engineAttention.length === 0 ? (
              <EmptyState title="Nothing flagged right now" />
            ) : (
              <ul className="space-y-3">
                {engineAttention.map((item, i) => (
                  <li key={i} className="flex flex-wrap items-center gap-3 rounded-xl border border-white/5 bg-white/5 p-4">
                    <AlertCircle className="h-5 w-5 shrink-0 text-warning" aria-hidden />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-zinc-200">
                        {item.entity} — {item.kind.replace(/_/g, " ")}
                      </p>
                      <p className="text-xs text-zinc-400">{item.evidence}</p>
                    </div>
                    <Link
                      href={KIND_SCREEN[item.kind] ?? "/fire-drill"}
                      className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary hover:bg-primary/20"
                    >
                      Run a fire drill
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="glass rounded-2xl p-6">
            <h2 className="mb-1 text-lg font-semibold">Today&apos;s reminders</h2>
            <p className="mb-4 text-xs text-zinc-500">
              Demo reminders from <code>/api/attention</code> — a hard-coded stub, not engine output.
            </p>
            <ul className="space-y-3">
              {attention.map((item) => (
                <li key={item.id} className="flex items-center gap-4 rounded-xl border border-white/5 bg-white/5 p-4">
                  <AlertCircle className="h-5 w-5 shrink-0 text-warning" aria-hidden />
                  <span className="flex-1 text-sm">{item.text}</span>
                  <Link
                    href="/fire-drill"
                    className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary hover:bg-primary/20"
                  >
                    Open Fire Drill
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Supplier dependency + stock cover */}
        <div className="space-y-6">
          <div className="glass rounded-2xl p-6">
            <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
              <BarChart3 className="h-5 w-5 text-primary" aria-hidden /> Supplier dependency
            </h2>
            {dep.length === 0 ? (
              <EmptyState title="No supplier data" />
            ) : (
              <ul className="space-y-4">
                {dep.map((d) => (
                  <li key={d.supplier_id}>
                    <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-zinc-200">{d.supplier}</span>
                      <ConcentrationChip level={d.concentration} />
                    </div>
                    <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/5">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${Math.min(100, d.purchase_value_share_pct)}%` }}
                      />
                    </div>
                    <p className="mt-1 font-mono text-[11px] text-zinc-500">
                      {d.purchase_value_share_pct}% of purchases · {d.stock_value_share_pct}% of stock value
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="glass rounded-2xl p-6">
            <h2 className="mb-4 text-lg font-semibold">Stock cover</h2>
            {cover.length === 0 ? (
              <EmptyState title="No stock data" />
            ) : (
              <ul className="space-y-3">
                {cover.map((c) => (
                  <li key={c.product_id} className="rounded-xl border border-white/5 bg-white/5 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-zinc-200">{c.product}</span>
                      <StatusChip status={c.status} />
                    </div>
                    <p className="mt-1 font-mono text-xs text-zinc-400">
                      {c.stock_units} units · {c.daily_demand}/day · cover {c.cover_days} days · restock day{" "}
                      {c.next_restock_day}
                    </p>
                    <p className="text-xs text-zinc-500">Runs out around day {c.days_to_stockout} without restock</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
