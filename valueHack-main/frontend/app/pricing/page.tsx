"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Line, LineChart, ReferenceDot, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from "recharts";
import { getPricingWhatIf, getBusiness, getForecast } from "@/lib/api";
import type { PricingWhatIf, ForecastResponse } from "@/lib/types";
import { formatInr, formatPct } from "@/lib/format";
import { EstimateBadge, SourceTag } from "@/components/ui/badges";
import { ErrorState, EmptyState, LoadingSkeleton } from "@/components/ui/states";
import { GlassCard } from "@/components/ui/GlassCard";
import { ChevronDown, ChevronUp, Sparkles, Brain } from "lucide-react";

type ElasticityCase = "low" | "base" | "high";

const tooltipStyle = {
  backgroundColor: "var(--card)",
  border: "1px solid var(--card-border)",
  borderRadius: 12,
  fontSize: 12,
  color: "var(--foreground)",
};

export default function PricingPage() {
  const [products, setProducts] = useState<Array<{ product_id: string; product: string }>>([]);
  const [productId, setProductId] = useState<string>("");
  const [elCase, setElCase] = useState<ElasticityCase>("base");
  const [pricePct, setPricePct] = useState(10);
  const [data, setData] = useState<PricingWhatIf | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [showAboutModel, setShowAboutModel] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    Promise.all([getBusiness(), getForecast()])
      .then(([b, f]) => {
        const list = (b.analytics?.stock_cover ?? []).map((c) => ({ product_id: c.product_id, product: c.product }));
        setProducts(list);
        if (list.length > 0) setProductId((p) => p || list[0].product_id);
        setForecast(f);
      })
      .catch((e) => setError(e));
  }, []);

  const fetchWhatIf = useCallback(
    async (pid: string, pct: number, ec: ElasticityCase) => {
      if (!pid) return;
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      setLoading(true);
      setError(null);
      try {
        const res = await getPricingWhatIf({ product_id: pid, price_change_pct: pct, elasticity: undefined }, ctrl.signal);
        const elValue = res.elasticity?.[ec];
        const res2 = elValue === res.elasticity?.base ? res : await getPricingWhatIf({ product_id: pid, price_change_pct: pct, elasticity: elValue }, ctrl.signal);
        setData(res2);
      } catch (e) {
        if (!(e instanceof DOMException && e.name === "AbortError")) setError(e);
      } finally {
        if (!ctrl.signal.aborted) setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (productId) fetchWhatIf(productId, pricePct, elCase);
  }, [productId, elCase]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const curvePoint = data?.curve.find((c) => c.price_change_pct === pricePct) ?? data?.curve[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mx-auto max-w-4xl space-y-8"
    >
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-card-border pb-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">Price what-if</h1>
          <p className="text-xs text-muted-foreground mt-1">
            An estimate from assumed price elasticity — not a prediction. The owner decides.
          </p>
        </div>
        <EstimateBadge />
      </div>

      {error ? <ErrorState error={error} title="Could not load pricing" onRetry={() => fetchWhatIf(productId, pricePct, elCase)} /> : null}

      <GlassCard className="p-6 space-y-6">
        {/* Product & Elasticity Pickers */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="product-picker" className="mb-1.5 block text-xs font-semibold text-muted-foreground">Product SKU</label>
            <select
              id="product-picker"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              className="w-full rounded-xl border border-card-border bg-card px-3.5 py-2.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
            >
              {products.map((p) => (
                <option key={p.product_id} value={p.product_id}>{p.product}</option>
              ))}
            </select>
          </div>

          <div>
            <p className="mb-1.5 text-xs font-semibold text-muted-foreground">Elasticity Scenario Case</p>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Elasticity case">
              {(["low", "base", "high"] as ElasticityCase[]).map((c) => (
                <button
                  key={c}
                  onClick={() => setElCase(c)}
                  aria-pressed={elCase === c}
                  className={`min-h-[44px] rounded-xl border px-4 py-2 text-xs font-bold capitalize transition-all ${
                    elCase === c ? "border-primary bg-primary/20 text-primary shadow-xs" : "border-card-border bg-card/60 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {c} case
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Price Slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="price-slider" className="text-xs font-semibold text-muted-foreground">
              Price Adjustment Slider
            </label>
            <span className="font-mono text-sm font-extrabold text-primary font-tabular">
              {pricePct > 0 ? `+${pricePct}` : pricePct}%
            </span>
          </div>
          <input
            id="price-slider"
            type="range"
            min={-20}
            max={20}
            step={2}
            value={pricePct}
            onChange={(e) => setPricePct(Number(e.target.value))}
            className="w-full accent-primary h-2 bg-muted rounded-lg cursor-pointer"
          />
        </div>

        {loading && !data ? (
          <LoadingSkeleton rows={4} className="h-40" />
        ) : !data || !curvePoint ? (
          <EmptyState title="Pick a product to see the estimate" />
        ) : (
          <div className="space-y-6 pt-2">
            {/* Metrics Row */}
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div className="rounded-xl border border-card-border bg-muted/40 p-3.5">
                <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Profit at +{pricePct}%</p>
                <p className="mt-1 font-mono text-base font-bold text-foreground font-tabular">{formatInr(data.profit_inr.base)}</p>
              </div>
              <div className="rounded-xl border border-card-border bg-muted/40 p-3.5">
                <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Profit Range (Low–High)</p>
                <p className="mt-1 font-mono text-xs font-bold text-foreground font-tabular">
                  {formatInr(curvePoint.profit_inr.low)} … {formatInr(curvePoint.profit_inr.high)}
                </p>
              </div>
              <div className="rounded-xl border border-card-border bg-muted/40 p-3.5">
                <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Base Profit at Slider</p>
                <p className="mt-1 font-mono text-base font-bold text-foreground font-tabular">{formatInr(curvePoint.profit_inr.base)}</p>
              </div>
              <div className="rounded-xl border border-card-border bg-muted/40 p-3.5">
                <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Break-even Demand Drop</p>
                <p className="mt-1 font-mono text-base font-bold text-primary font-tabular">{formatPct(data.breakeven_demand_drop_pct)}</p>
              </div>
            </div>

            {/* Highlighted Insight Callout */}
            <div className="rounded-2xl border border-primary/30 bg-primary/10 p-4 space-y-1">
              <div className="flex items-center gap-2 text-xs font-bold text-primary uppercase tracking-wider">
                <Sparkles className="w-4 h-4" /> Engine Insight Callout
              </div>
              <p className="text-xs text-foreground font-medium leading-relaxed">{data.sentence}</p>
            </div>

            {/* Elasticity Line Chart */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Profit Elasticity Curve</h3>
              <div className="h-[360px] w-full pt-4" role="img" aria-label="Profit by price change chart">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.curve} margin={{ top: 10, right: 24, left: 16, bottom: 20 }}>
                    <XAxis dataKey="price_change_pct" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} unit="%" />
                    <YAxis stroke="var(--muted-foreground)" fontSize={11} tickLine={false} tickFormatter={(v) => `₹${Math.round(Number(v) / 1000)}k`} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend wrapperStyle={{ paddingTop: 10, fontSize: 11 }} />
                    <ReferenceLine x={0} stroke="var(--card-border)" strokeWidth={1.5} />
                    <ReferenceLine x={pricePct} stroke="var(--primary)" strokeDasharray="3 3" />
                    <Line type="monotone" dataKey="profit_inr.low" name="Low elasticity" stroke="#94A3B8" strokeWidth={1.5} dot={false} />
                    <Line type="monotone" dataKey="profit_inr.base" name="Base elasticity" stroke="#8B5CF6" strokeWidth={2.5} dot={false} />
                    <Line type="monotone" dataKey="profit_inr.high" name="High elasticity" stroke="#3B82F6" strokeWidth={1.5} dot={false} />
                    <ReferenceDot x={pricePct} y={curvePoint.profit_inr.base} r={6} fill="#8B5CF6" stroke="var(--card)" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Assumptions List */}
            <ul className="space-y-2">
              {data.assumptions.map((a) => (
                <li key={a.id} className="flex items-center gap-2.5 rounded-xl border border-card-border bg-muted/30 p-3">
                  <SourceTag source={a.source} />
                  <span className="text-xs text-muted-foreground">{a.text}</span>
                </li>
              ))}
            </ul>

            {/* Collapsible About the Model Card */}
            <div className="border-t border-card-border pt-4">
              <button
                onClick={() => setShowAboutModel(!showAboutModel)}
                className="flex items-center justify-between w-full py-2 text-xs font-bold text-foreground hover:text-primary transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-primary" /> About the Forecasting & Elasticity Model
                </span>
                {showAboutModel ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showAboutModel && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="mt-3 rounded-2xl border border-card-border bg-muted/40 p-4 space-y-3 text-xs text-muted-foreground leading-relaxed"
                >
                  <p>
                    <strong>Methodology:</strong> Exponential Smoothing (Holt-Winters) trained on 90 days of synthetic sales history.
                  </p>
                  {forecast && (
                    <div className="p-3 rounded-xl bg-card border border-card-border font-mono text-[11px]">
                      <span>Model: {forecast.method}</span>
                      <br />
                      <span>14-day Holdout Backtest MAPE: <strong>{forecast.overall_mape}%</strong></span>
                    </div>
                  )}
                  <p>
                    Elasticity values (low, base, high) are assumed bounded parameters. Prices can be adjusted in real-time without re-fetching API data.
                  </p>
                </motion.div>
              )}
            </div>
          </div>
        )}
      </GlassCard>
    </motion.div>
  );
}
