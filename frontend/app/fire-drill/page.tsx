"use client";
import { useState, useCallback } from 'react';
import { simulateCascade, compareActions } from '@/lib/api';
import { LineChart, Line, ReferenceLine, ResponsiveContainer, YAxis, XAxis, Tooltip } from 'recharts';
import { Play } from 'lucide-react';

interface SimResult {
  stockout: number | null;
  first_negative_day: number | null;
  min_cash: number;
  failed: Array<{ name: string; day: number }>;
  cash_timeline: number[];
}

interface ActionResult {
  min_cash: number;
  failed: Array<{ name: string; day: number }>;
  cash_timeline: number[];
}

interface ActionsResult {
  do_nothing: ActionResult;
  ask_extension: ActionResult;
  early_discount: ActionResult;
  switch_vendor: ActionResult;
  combined: ActionResult;
}

export default function FireDrill() {
  const [delay, setDelay] = useState(14);
  const [simResult, setSimResult] = useState<SimResult | null>(null);
  const [actionsResult, setActionsResult] = useState<ActionsResult | null>(null);

  const runSim = useCallback(async (d: number) => {
    try {
      const res = await simulateCascade({ delay: d });
      setSimResult(res);
      const acts = await compareActions(d);
      setActionsResult(acts);
    } catch (e) {
      console.error(e);
    }
  }, []);

  const handleDelayChange = (val: number) => {
    setDelay(val);
  };

  const chartData = simResult?.cash_timeline.map((c: number, i: number) => ({
    day: i + 1,
    cash: c,
    actionCash: actionsResult?.combined?.cash_timeline[i] ?? c,
    baseline: 50000 - (i * 3000),
  })) || [];

  return (
    <div className="flex flex-col md:flex-row gap-6 min-h-[calc(100vh-8rem)]">
      {/* Left: Params */}
      <div className="w-full md:w-80 glass p-6 rounded-2xl flex flex-col gap-6 overflow-y-auto">
        <h2 className="text-xl font-bold">Scenario Setup</h2>
        <div>
          <label className="text-sm text-zinc-400 mb-2 block">Supplier Delay (Days)</label>
          <input
            type="range" min="0" max="30" value={delay}
            onChange={e => handleDelayChange(Number(e.target.value))}
            className="w-full accent-primary"
          />
          <div className="text-right font-mono mt-1">{delay} days</div>
        </div>
        <button onClick={() => runSim(delay)} className="w-full py-3 rounded-xl bg-primary text-white font-bold flex items-center justify-center gap-2 hover:bg-primary/90 transition">
          <Play className="w-4 h-4" /> Run Simulation
        </button>
        {!simResult && (
          <p className="text-xs text-zinc-500 text-center">Click Run Simulation to begin</p>
        )}
      </div>

      {/* Center & Right */}
      <div className="flex-1 flex flex-col gap-6 overflow-hidden">
        {/* Cascade Map */}
        <div className="flex-1 glass rounded-2xl p-6 relative flex flex-col items-center justify-center border border-white/5 min-h-48">
          <h3 className="absolute top-6 left-6 font-semibold text-sm text-zinc-400 uppercase tracking-wider">Cascade Flow</h3>
          <div className="flex flex-wrap items-center justify-center gap-4 text-sm font-medium mt-8">
            {[
              { label: 'Supplier A', state: 'danger', detail: delay > 0 ? `+${delay}d late` : 'On time' },
              { label: 'Stock', state: simResult?.stockout ? 'danger' : 'safe', detail: simResult?.stockout ? `Out day ${simResult.stockout}` : '—' },
              { label: 'Orders', state: simResult?.stockout ? 'warning' : 'safe', detail: simResult?.stockout ? 'Delayed' : '—' },
              { label: 'Cash', state: simResult?.first_negative_day ? 'danger' : 'safe', detail: simResult?.first_negative_day ? `Neg day ${simResult.first_negative_day}` : '—' },
              { label: 'Payables', state: simResult?.failed?.length ? 'danger' : 'safe', detail: simResult?.failed?.length ? `${simResult.failed.length} failed` : '—' },
            ].map((node, i, arr) => (
              <div key={node.label} className="flex items-center gap-2">
                <div className={`p-4 rounded-xl border text-center min-w-[100px] ${
                  node.state === 'danger' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                  node.state === 'warning' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                  'bg-white/5 text-zinc-300 border-white/10'
                }`}>
                  <div className="font-semibold">{node.label}</div>
                  <div className="text-xs mt-1 opacity-80">{node.detail}</div>
                </div>
                {i < arr.length - 1 && (
                  <div className={`w-6 h-0.5 ${node.state !== 'safe' ? 'bg-red-500/50' : 'bg-white/20'}`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Cash Chart */}
        <div className="glass p-6 rounded-2xl">
          <h3 className="font-semibold mb-4 text-sm text-zinc-400 uppercase tracking-wider">Cash Runway</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: 20, bottom: 0 }}>
                <XAxis dataKey="day" stroke="#A1A1AA" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#A1A1AA" fontSize={11} tickLine={false} axisLine={false} tickFormatter={v => `₹${Math.round(v / 1000)}k`} />
                <Tooltip contentStyle={{ backgroundColor: '#12121A', borderColor: 'rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
                <ReferenceLine y={0} stroke="#EF4444" strokeDasharray="4 4" label={{ position: 'right', value: '₹0', fill: '#EF4444', fontSize: 11 }} />
                {simResult?.first_negative_day && (
                  <ReferenceLine x={simResult.first_negative_day} stroke="#EF4444" strokeDasharray="4 4"
                    label={{ position: 'top', value: `Day ${simResult.first_negative_day}`, fill: '#EF4444', fontSize: 11 }} />
                )}
                <Line type="monotone" dataKey="baseline" stroke="#71717A" strokeWidth={1.5} dot={false} name="Baseline" strokeDasharray="4 4" />
                <Line type="monotone" dataKey="cash" stroke="#EF4444" strokeWidth={2} dot={false} name="Disrupted" />
                <Line type="monotone" dataKey="actionCash" stroke="#22C55E" strokeWidth={2} dot={false} name="After Action" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          {simResult && (
            <div className="mt-4 flex gap-4 text-xs">
              <div className="flex items-center gap-1.5"><div className="w-3 h-0.5 bg-zinc-500 rounded" /> Baseline</div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-0.5 bg-red-500 rounded" /> Disrupted</div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-0.5 bg-green-500 rounded" /> After Action</div>
            </div>
          )}
        </div>

        {/* Actions Grid */}
        {actionsResult && (
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            {(Object.entries(actionsResult) as [string, ActionResult][]).map(([key, res]) => (
              <div key={key} className={`p-4 rounded-xl border ${key === 'combined' ? 'border-primary/50 bg-primary/10' : 'border-white/5 bg-white/5'}`}>
                <div className="flex justify-between items-start mb-2 gap-1">
                  <h4 className="font-semibold capitalize text-xs leading-tight">{key.replace(/_/g, ' ')}</h4>
                  {key === 'combined' && <span className="text-[9px] uppercase font-bold text-primary bg-primary/20 px-1.5 py-0.5 rounded-full whitespace-nowrap">✓ Best</span>}
                </div>
                <p className="text-xs text-zinc-400">Min: ₹{Math.round(res.min_cash).toLocaleString()}</p>
                <p className="text-xs text-zinc-400">Fails: {res.failed.length}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
