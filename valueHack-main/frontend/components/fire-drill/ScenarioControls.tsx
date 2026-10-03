"use client";

import { useState } from "react";
import { Loader2, ScrollText, Sparkles } from "lucide-react";
import { parseScenario } from "@/lib/api";
import type { ScenarioType } from "@/lib/types";
import { ErrorState } from "@/components/ui/states";

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

const SAMPLE_CHIPS = [
  { text: "Supplier A is 14 days late", type: "supplier_delay" as ScenarioType, target: "A", mag: 14 },
  { text: "Customer pays 20 days late", type: "customer_delay" as ScenarioType, target: "Verma", mag: 20 },
  { text: "Cost up 15%", type: "cost_spike" as ScenarioType, target: "", mag: 15 },
];

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
          `Parsed: ${t.replace(/_/g, " ")}${res.target ? `, target ${res.target}` : ""}, ${res.days ?? magnitude} ${
            t === "cost_spike" ? "%" : "days"
          }.`
        );
      } else {
        setParseNote(`Parser returned "${res.type}" — fill controls manually.`);
      }
    } catch (e) {
      setParseError(e);
    } finally {
      setParsing(false);
    }
  };

  const applyChip = (chip: typeof SAMPLE_CHIPS[0]) => {
    setScenarioText(chip.text);
    onApplyParsed(chip.type, chip.target, chip.mag);
  };

  return (
    <div className="flex flex-col gap-5 text-left">
      <div>
        <h2 className="text-lg font-bold text-foreground">Scenario Setup</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">Deterministic simulation parameters</p>
      </div>

      {/* Plain-language box with example chips */}
      <div className="space-y-2">
        <label htmlFor="scenario-text" className="block text-xs font-semibold text-muted-foreground">
          Describe disruption in plain words
        </label>
        <textarea
          id="scenario-text"
          rows={2}
          value={scenarioText}
          onChange={(e) => setScenarioText(e.target.value)}
          placeholder="e.g. Supplier A is 14 days late"
          className="w-full resize-none rounded-xl border border-card-border bg-card p-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
        />

        {/* Preset Chips */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          {SAMPLE_CHIPS.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => applyChip(chip)}
              className="inline-flex items-center gap-1 rounded-full border border-card-border bg-muted/50 px-2.5 py-1 text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
            >
              <Sparkles className="w-3 h-3 text-primary" /> {chip.text}
            </button>
          ))}
        </div>

        <button
          onClick={handleParse}
          disabled={parsing || scenarioText.trim().length === 0}
          className="mt-2 min-h-[44px] flex w-full items-center justify-center gap-2 rounded-xl bg-primary text-white font-bold text-xs shadow-md hover:bg-primary/90 transition-all disabled:opacity-50"
        >
          {parsing ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <ScrollText className="h-4 w-4" aria-hidden />}
          {parsing ? "Parsing Scenario..." : "Fill Controls from Text"}
        </button>

        {parseError ? (
          <div className="mt-2">
            <ErrorState error={parseError} title="Could not read text" onRetry={() => setParseError(null)} />
          </div>
        ) : null}
        {parseNote && <p className="mt-2 rounded-xl bg-primary/10 border border-primary/20 p-2 text-xs text-primary font-medium">{parseNote}</p>}
      </div>

      {/* Scenario Type Radio Selector */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-muted-foreground">Scenario Type</p>
        <div className="grid grid-cols-1 gap-1.5">
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
              className={`min-h-[44px] flex items-center justify-between rounded-xl border px-3.5 text-xs font-bold transition-all ${
                type === t.id
                  ? "border-primary bg-primary/15 text-primary"
                  : "border-card-border bg-card/60 text-muted-foreground hover:text-foreground"
              }`}
            >
              <span>{t.label}</span>
              {type === t.id && <span className="h-2 w-2 rounded-full bg-primary" />}
            </button>
          ))}
        </div>
      </div>

      {/* Target Input */}
      {type !== "cost_spike" && (
        <div className="space-y-1">
          <label htmlFor="scenario-target" className="block text-xs font-semibold text-muted-foreground">
            {type === "supplier_delay" ? "Supplier Name / Code (e.g. A)" : "Customer Name"}
          </label>
          <input
            id="scenario-target"
            type="text"
            value={target}
            onChange={(e) => onChange({ target: e.target.value })}
            className="w-full rounded-xl border border-card-border bg-card px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
          />
        </div>
      )}

      {/* Magnitude Slider */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label htmlFor="scenario-magnitude" className="text-xs font-semibold text-muted-foreground">
            {type === "cost_spike" ? "Cost Increase" : "Disruption Duration"}
          </label>
          <span className="font-mono text-xs font-bold text-primary font-tabular">
            {magnitude} {range.unit}
          </span>
        </div>
        <input
          id="scenario-magnitude"
          type="range"
          min={0}
          max={range.max}
          value={magnitude}
          onChange={(e) => onChange({ magnitude: Number(e.target.value) })}
          className="w-full accent-primary h-2 bg-muted rounded-lg appearance-none cursor-pointer"
        />
      </div>

      {/* Demand Band Slider */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label htmlFor="demand-band" className="text-xs font-semibold text-muted-foreground">
            Demand Variance Band
          </label>
          <span className="font-mono text-xs font-bold text-primary font-tabular">±{demandBand}%</span>
        </div>
        <input
          id="demand-band"
          type="range"
          min={0}
          max={50}
          step={5}
          value={demandBand}
          onChange={(e) => onChange({ demandBand: Number(e.target.value) })}
          className="w-full accent-primary h-2 bg-muted rounded-lg appearance-none cursor-pointer"
        />
      </div>
    </div>
  );
}
