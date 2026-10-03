"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Line, LineChart, ReferenceDot, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getPricingWhatIf, getBusiness } from "@/lib/api";
import type { PricingWhatIf } from "@/lib/types";
import { formatInr, formatPct } from "@/lib/format";
import { EstimateBadge, SourceTag } from "@/components/ui/badges";
import { ErrorState, EmptyState, LoadingSkeleton } from "@/components/ui/states";

/**
 * Price what-if. The slider (−20…+20, step 2) reads the engine's precomputed
 * `curve` — moving it never calls the API. The API is called again only when
 * the product or the elasticity case changes. Elasticity is an assumption
 * (the backend labels it source: "assumed").
 */

type ElasticityCase = "low" | "base" | "high";

const tooltipStyle = {
  backgroundColor: "#12121A",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  fontSize: 12,
};

export default function PricingPage() {
  const [products, setProducts] = useState<Array<{ product_id: string; product: string }>>([]);
  const [productId, setProductId] = useState<string>("");
  const [elCase, setElCase] = useState<ElasticityCase>("base");
  const [pricePct, setPricePct] = useState(10);
  const [data, setData] = useState<PricingWhatIf | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    getBusiness()
      .then((b) => {
        const list = (b.analytics?.stock_cover ?? []).map((c) => ({ product_id: c.product_id, product: c.product }));
        setProducts(list);
        if (list.length > 0) setProductId((p) => p || list[0].product_id);
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
        // Re-request with the chosen band from the response (never a UI-made number).
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId, elCase]);

  useEffect(() => () => abortRef.current?.abort(), []);

  // Slider reads the curve — no fetch.
  const curvePoint = data?.curve.find((c) => c.price_change_pct === pricePct) ?? data?.curve[0];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Price what-if</h1>
          <p className="text-sm text-zinc-500">
            An estimate from an assumed price elasticity — not a prediction. The owner decides.
          </p>
        </div>
        <EstimateBadge />
      </div>

      {error ? <ErrorState error={error} title="Could not load pricing" onRetry={() => fetchWhatIf(productId, pricePct, elCase)} /> : null}

      <div className="glass rounded-2xl p-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="product-picker" className="mb-1.5 block text-sm text-zinc-400">Product</label>
            <select
              id="product-picker"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            >
              {products.map((p) => (
                <option key={p.product_id} value={p.product_id} className="bg-zinc-900">{p.product}</option>
              ))}
            </select>
          </div>
          <div>
            <p className="mb-1.5 text-sm text-zinc-400">Elasticity case <span className="text-zinc-600">(assumption)</span></p>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Elasticity case">
              {(["low", "base", "high"] as ElasticityCase[]).map((c) => (
                <button
                  key={c}
                  onClick={() => setElCase(c)}
                  aria-pressed={elCase === c}
                  className={`rounded-full border px-3.5 py-1.5 text-sm font-medium capitalize transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary ${
                    elCase === c ? "border-primary bg-primary/20 text-primary" : "border-white/10 bg-white/5 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6">
          <label htmlFor="price-slider" className="mb-1.5 block text-sm text-zinc-400">
            Price change: <span className="font-mono text-zinc-200">{pricePct > 0 ? `+${pricePct}` : pricePct}%</span>
          </label>
          <input
            id="price-slider"
            type="range"
            min={-20}
            max={20}
            step={2}
            value={pricePct}
            onChange={(e) => setPricePct(Number(e.target.value))}
            className="w-full accent-primary"
            aria-valuetext={`${pricePct} percent`}
          />
        </div>

        {loading && !data ? (
          <LoadingSkeleton rows={3} className="h-20" />
        ) : error ? null : !data || !curvePoint ? (
          <EmptyState title="Pick a product to see the estimate" />
        ) : (
          <div className="mt-6 space-y-5">
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div className="rounded-xl border border-white/5 bg-white/5 p-3">
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">Profit at +{pricePct}% (loaded case)</p>
                <p className="mt-1 font-mono text-sm text-zinc-100">{formatInr(data.profit_inr.base)}</p>
              </div>
              <div className="rounded-xl border border-white/5 bg-white/5 p-3">
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">Profit change (low–high)</p>
                <p className="mt-1 font-mono text-sm text-zinc-100">
                  {formatInr(curvePoint.profit_inr.low)} … {formatInr(curvePoint.profit_inr.high)}
                </p>
              </div>
              <div className="rounded-xl border border-white/5 bg-white/5 p-3">
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">Base profit at slider</p>
                <p className="mt-1 font-mono text-sm text-zinc-100">{formatInr(curvePoint.profit_inr.base)}</p>
              </div>
              <div className="rounded-xl border border-white/5 bg-white/5 p-3">
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">Break-even demand drop (loaded)</p>
                <p className="mt-1 font-mono text-sm text-zinc-100">{formatPct(data.breakeven_demand_drop_pct)}</p>
              </div>
            </div>

            <p className="rounded-xl border border-white/5 bg-white/5 p-3 text-sm text-zinc-300">
              <span className="font-semibold text-primary">Engine says: </span>
              {data.sentence}
            </p>
            <p className="text-xs text-zinc-500">
              Break-even and the sentence describe the loaded price point ({data.price_change_pct > 0 ? "+" : ""}
              {data.price_change_pct}%); the slider profit figures come straight from the precomputed curve.
            </p>

            <div className="h-56" role="img" aria-label="Profit by price change chart">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.curve} margin={{ top: 10, right: 16, left: 4, bottom: 0 }}>
                  <XAxis dataKey="price_change_pct" stroke="#A1A1AA" fontSize={11} tickLine={false} axisLine={false} unit="%" />
                  <YAxis stroke="#A1A1AA" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `₹${Math.round(Number(v) / 1000)}k`} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <ReferenceLine x={0} stroke="rgba(255,255,255,0.2)" />
                  <ReferenceLine x={pricePct} stroke="#7C5CFF" strokeDasharray="2 3" />
                  <Line type="monotone" dataKey="profit_inr.low" name="Low elasticity" stroke="#71717A" strokeWidth={1.4} dot={false} />
                  <Line type="monotone" dataKey="profit_inr.base" name="Base elasticity" stroke="#7C5CFF" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="profit_inr.high" name="High elasticity" stroke="#4F9DFF" strokeWidth={1.4} dot={false} />
                  <ReferenceDot x={pricePct} y={curvePoint.profit_inr.base} r={5} fill="#7C5CFF" stroke="#0A0A0F" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <ul className="space-y-2">
              {data.assumptions.map((a) => (
                <li key={a.id} className="flex flex-wrap items-center gap-2 rounded-xl border border-white/5 bg-white/5 p-3">
                  <SourceTag source={a.source} />
                  <span className="text-sm text-zinc-300">{a.text}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
