"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { AlertCircle, BarChart3, Wallet, PackageCheck, AlertTriangle, Building2, ArrowUpRight, Info } from "lucide-react";
import { getBusiness, getAttention } from "@/lib/api";
import type { AttentionItem, BusinessResponse } from "@/lib/types";
import { formatInr } from "@/lib/format";
import { ConcentrationChip, EstimateBadge, StatusChip } from "@/components/ui/badges";
import { EmptyState, ErrorState, LoadingSkeleton } from "@/components/ui/states";
import { GlassCard } from "@/components/ui/GlassCard";
import { StatCard } from "@/components/ui/StatCard";

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
            <LoadingSkeleton key={i} rows={1} className="h-28" />
          ))}
        </div>
        <LoadingSkeleton rows={3} className="h-16" />
      </div>
    );
  }

  const dep = business.analytics?.dependency_shares?.supplier_dependency ?? [];
  const cover = business.analytics?.stock_cover ?? [];

  // Deduplicate engine attention items by unique entity + kind + evidence
  const rawAttention = business.analytics?.attention_inputs ?? [];
  const engineAttention = rawAttention.filter(
    (item, index, self) =>
      index === self.findIndex((t) => t.entity === item.entity && t.kind === item.kind && t.evidence === item.evidence)
  );

  const atRisk = cover.filter((c) => c.status !== "safe").length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-card-border pb-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">{business.name}</h1>
          <p className="text-xs text-muted-foreground mt-1">Synthetic demo business · estimates from deterministic simulation</p>
        </div>
        <div className="flex items-center gap-3">
          <EstimateBadge />
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          title="Cash on hand"
          value={business.cash}
          isCurrency
          subtitle="Fixed burn ₹3,000/day"
          icon={<Wallet className="w-5 h-5" />}
        />
        <StatCard
          title="Products tracked"
          value={cover.length}
          subtitle="Active catalog SKUs"
          icon={<PackageCheck className="w-5 h-5" />}
        />
        <StatCard
          title="Products at risk"
          value={atRisk}
          subtitle="Watch or critical cover"
          icon={<AlertTriangle className="w-5 h-5" />}
        />
        <StatCard
          title="Active suppliers"
          value={dep.length}
          subtitle="Primary: Supplier A"
          icon={<Building2 className="w-5 h-5" />}
        />
      </div>

      {/* Main Grid Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Attention & Reminders */}
        <div className="space-y-6 lg:col-span-2">
          {/* Engine Attention */}
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-warning" /> Needs attention (Engine Analytics)
              </h2>
              <span className="text-xs font-semibold text-muted-foreground">{engineAttention.length} Unique Flagged</span>
            </div>

            {engineAttention.length === 0 ? (
              <EmptyState title="Nothing flagged right now" />
            ) : (
              <ul className="space-y-3">
                {engineAttention.map((item, i) => (
                  <li
                    key={i}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-card-border bg-muted/40 p-4 transition-all hover:bg-muted/60"
                  >
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <AlertCircle className="h-4 w-4 shrink-0 text-warning mt-0.5" aria-hidden />
                      <div>
                        <p className="text-xs font-bold text-foreground">
                          {item.entity} — <span className="capitalize">{item.kind.replace(/_/g, " ")}</span>
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">{item.evidence}</p>
                      </div>
                    </div>
                    <Link
                      href={`${KIND_SCREEN[item.kind] ?? "/fire-drill"}?target=${encodeURIComponent(item.entity)}`}
                      className="inline-flex items-center gap-1 rounded-lg bg-primary/10 border border-primary/20 px-3 py-1.5 text-xs font-bold text-primary hover:bg-primary/20 transition-all shrink-0"
                    >
                      Run Fire Drill <ArrowUpRight className="w-3.5 h-3.5" />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </GlassCard>

          {/* Today's Reminders */}
          <GlassCard>
            <div className="mb-4">
              <h2 className="text-base font-bold text-foreground">Today&apos;s reminders</h2>
              <p className="text-xs text-muted-foreground">Demo reminders fed from <code>/api/attention</code></p>
            </div>
            <ul className="space-y-3">
              {attention.map((item) => (
                <li key={item.id} className="flex items-center gap-3 rounded-xl border border-card-border bg-muted/40 p-3.5">
                  <AlertCircle className="h-4 w-4 shrink-0 text-warning" aria-hidden />
                  <span className="flex-1 text-xs text-foreground font-medium">{item.text}</span>
                  <Link
                    href="/fire-drill"
                    className="rounded-lg bg-primary/10 border border-primary/20 px-3 py-1 text-xs font-bold text-primary hover:bg-primary/20 transition-all"
                  >
                    Fire Drill
                  </Link>
                </li>
              ))}
            </ul>
          </GlassCard>
        </div>

        {/* Right Column: Supplier Dependency & Stock Cover Gauges */}
        <div className="space-y-6">
          {/* Supplier Dependency */}
          <GlassCard>
            <h2 className="mb-4 flex items-center gap-2 text-base font-bold text-foreground">
              <BarChart3 className="h-4 w-4 text-primary" aria-hidden /> Supplier dependency
            </h2>
            {dep.length === 0 ? (
              <EmptyState title="No purchase data" />
            ) : (
              <ul className="space-y-4">
                {dep.map((d) => (
                  <li key={d.supplier_id} title={`Purchase value share: ${d.purchase_value_share_pct}% | Stock value share: ${d.stock_value_share_pct}%`}>
                    <div className="mb-1.5 flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-foreground flex items-center gap-1">
                        {d.supplier} <Info className="w-3 h-3 text-muted-foreground" />
                      </span>
                      <ConcentrationChip level={d.concentration} />
                    </div>
                    <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary transition-all duration-700"
                        style={{ width: `${Math.max(5, Math.min(100, d.purchase_value_share_pct))}%` }}
                      />
                    </div>
                    <p className="mt-1 font-mono text-[11px] text-muted-foreground font-tabular">
                      {d.purchase_value_share_pct}% purchases · {d.stock_value_share_pct}% stock value
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </GlassCard>

          {/* Stock Cover Gauges */}
          <GlassCard>
            <h2 className="mb-4 text-base font-bold text-foreground">Stock cover gauges</h2>
            {cover.length === 0 ? (
              <EmptyState title="No stock data" />
            ) : (
              <ul className="space-y-4">
                {cover.map((c) => {
                  const coverRatio = Math.min(100, Math.round((c.cover_days / 30) * 100));
                  const statusColor = c.status === "critical" ? "bg-red-500" : c.status === "watch" ? "bg-amber-500" : "bg-green-500";

                  return (
                    <li key={c.product_id} className="rounded-xl border border-card-border bg-muted/40 p-3.5 space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-foreground">{c.product}</span>
                        <StatusChip status={c.status} />
                      </div>

                      {/* Visual Linear Gauge */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground font-tabular">
                          <span>{c.cover_days} days cover</span>
                          <span>Restock: Day {c.next_restock_day}</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                          <div className={`h-full rounded-full ${statusColor} transition-all duration-700`} style={{ width: `${coverRatio}%` }} />
                        </div>
                      </div>

                      <p className="text-[11px] text-muted-foreground font-mono font-tabular">
                        {c.stock_units} units in stock · {c.daily_demand}/day burn
                      </p>
                    </li>
                  );
                })}
              </ul>
            )}
          </GlassCard>
        </div>
      </div>
    </motion.div>
  );
}
