"use client";

import { useState } from "react";
import { Loader2, ScrollText } from "lucide-react";
import { parseScenario } from "@/lib/api";
import type { ScenarioType } from "@/lib/types";
import { ErrorState } from "@/components/ui/states";

/**
 * Scenario controls. The plain-language box calls /api/scenario/parse and
 * fills the controls from the parsed result — the owner can edit before the
 * run. The parser on the backend is a simple pattern-matcher (regex stub):
 * it currently recognises supplier-delay phrasing and returns
 * {type, target, days}; anything else is shown honestly.
 */

const TYPES: Array<{ id: ScenarioType; label: string }> = [
  { id: "supplier_delay", label: "Supplier delay" },
  { id: "customer_delay", label: "Customer delay" },
  { id: "cost_spike", label: "Cost spike" },
];

const MAG_RANGE: Record<ScenarioType, { max: number; unit: string }> = {
  supplier_delay: { max: 30, unit: "days" },
  customer_delay: { max: 30, unit: "days" },
  cost_spike: { max: 100, unit: "%" },
  demand_shock: { max: 100, unit: "%" },
};

export default function ScenarioControls({
  type,
  target,
  magnitude,
  demandBand,
  onChange,
  onApplyParsed,
}: {
  type: ScenarioType;
  target: string;
  magnitude: number;
  demandBand: number;
  onChange: (patch: { type?: ScenarioType; target?: string; magnitude?: number; demandBand?: number }) => void;
  onApplyParsed: (type: ScenarioType, target: string, magnitude: number) => void;
}) {
  const [scenarioText, setScenarioText] = useState("Supplier A is 14 days late");
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState<unknown>(null);
  const [parseNote, setParseNote] = useState<string | null>(null);
  const range = MAG_RANGE[type];

  const handleParse = async () => {
    setParsing(true);
    setParseError(null);
    setParseNote(null);
    try {
      const res = await parseScenario(scenarioText);
      const t = res.type as ScenarioType;
      if (t === "supplier_delay" || t === "customer_delay" || t === "cost_spike") {
        onApplyParsed(t, res.target ?? target, res.days ?? magnitude);
        setParseNote(
          `Parsed as: ${t.replace(/_/g, " ")}${res.target ? `, target ${res.target}` : ""}, ${res.days ?? magnitude} ${
            t === "cost_spike" ? "%" : "days"
          }. Edit below before running.`,
        );
      } else {
        setParseNote(`Parser returned "${res.type}" — this screen supports supplier delay, customer delay and cost spike, so fill the controls manually.`);
      }
    } catch (e) {
      setParseError(e);
    } finally {
      setParsing(false);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-lg font-bold">Scenario setup</h2>
        <p className="mt-1 text-xs text-zinc-500">Estimates from a deterministic simulation — not predictions.</p>
      </div>

      {/* Plain-language box */}
      <div>
        <label htmlFor="scenario-text" className="mb-1.5 block text-sm text-zinc-400">
          Describe it in plain words
        </label>
        <textarea
          id="scenario-text"
          rows={2}
          value={scenarioText}
          onChange={(e) => setScenarioText(e.target.value)}
          placeholder="e.g. Supplier A is 14 days late"
          className="w-full resize-none rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-zinc-200 placeholder:text-zinc-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
        />
        <button
          onClick={handleParse}
          disabled={parsing || scenarioText.trim().length === 0}
          className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl border border-primary/40 bg-primary/10 py-2 text-sm font-medium text-primary transition hover:bg-primary/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary disabled:opacity-50"
        >
          {parsing ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <ScrollText className="h-4 w-4" aria-hidden />}
          {parsing ? "Reading…" : "Fill the controls"}
        </button>
        {parseError ? (
          <div className="mt-2">
            <ErrorState error={parseError} title="Could not read that" onRetry={() => setParseError(null)} />
          </div>
        ) : null}
        {parseNote && <p className="mt-2 rounded-lg bg-white/5 p-2 text-xs text-zinc-400">{parseNote}</p>}
      </div>

      {/* Scenario type */}
      <div>
        <p className="mb-1.5 text-sm text-zinc-400">Scenario type</p>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Scenario type">
          {TYPES.map((t) => (
            <button
              key={t.id}
              onClick={() =>
                onChange({
                  type: t.id,
                  magnitude: t.id === "cost_spike" ? (type === "cost_spike" ? magnitude : 15) : magnitude,
                  target: t.id === "supplier_delay" && target.trim() === "" ? "A" : target,
                })
              }
              aria-pressed={type === t.id}
              className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary ${
                type === t.id
                  ? "border-primary bg-primary/20 text-primary"
                  : "border-white/10 bg-white/5 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Target (not needed for a cost spike) */}
      {type !== "cost_spike" && (
        <div>
          <label htmlFor="scenario-target" className="mb-1.5 block text-sm text-zinc-400">
            {type === "supplier_delay" ? "Supplier (name or A / B / C)" : "Customer name"}
          </label>
          <input
            id="scenario-target"
            type="text"
            value={target}
            onChange={(e) => onChange({ target: e.target.value })}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
          />
        </div>
      )}

      {/* Magnitude */}
      <div>
        <label htmlFor="scenario-magnitude" className="mb-1.5 block text-sm text-zinc-400">
          {type === "cost_spike" ? "Cost increase" : type === "customer_delay" ? "Days the customer pays late" : "Days the supplier is late"}
        </label>
        <input
          id="scenario-magnitude"
          type="range"
          min={0}
          max={range.max}
          value={magnitude}
          onChange={(e) => onChange({ magnitude: Number(e.target.value) })}
          className="w-full accent-primary"
          aria-valuetext={`${magnitude} ${range.unit}`}
        />
        <div className="mt-1 flex items-center gap-2">
          <input
            type="number"
            min={0}
            max={range.max}
            value={magnitude}
            onChange={(e) => onChange({ magnitude: Math.max(0, Math.min(range.max, Number(e.target.value) || 0)) })}
            className="w-20 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-right font-mono text-sm text-zinc-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
          />
          <span className="text-sm text-zinc-500">{range.unit}</span>
        </div>
      </div>

      {/* Demand band */}
      <div>
        <label htmlFor="demand-band" className="mb-1.5 block text-sm text-zinc-400">
          Demand range around the base case
        </label>
        <input
          id="demand-band"
          type="range"
          min={0}
          max={50}
          step={5}
          value={demandBand}
          onChange={(e) => onChange({ demandBand: Number(e.target.value) })}
          className="w-full accent-primary"
          aria-valuetext={`${demandBand} percent`}
        />
        <div className="text-right font-mono text-sm text-zinc-300">±{demandBand}%</div>
      </div>
    </div>
  );
}
