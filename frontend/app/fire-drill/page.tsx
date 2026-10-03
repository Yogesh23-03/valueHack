"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { simulateCascade, compareActions } from "@/lib/api";
import type { ActionsCompareResponse, CascadeResult, ScenarioType } from "@/lib/types";
import { formatCount, formatDay, formatInr } from "@/lib/format";
import { EstimateBadge } from "@/components/ui/badges";
import { ErrorState, LoadingSkeleton } from "@/components/ui/states";
import ScenarioControls from "@/components/fire-drill/ScenarioControls";
import CascadeMap from "@/components/fire-drill/CascadeMap";
import TimelinesChart from "@/components/fire-drill/TimelinesChart";
import WhyPanel from "@/components/fire-drill/WhyPanel";
import AssumptionsBox from "@/components/fire-drill/AssumptionsBox";
import RangesPanel from "@/components/fire-drill/RangesPanel";
import ActionsCompare from "@/components/fire-drill/ActionsCompare";

function buildRequest(type: ScenarioType, target: string, magnitude: number, demandBand: number) {
  const scenario = {
    type,
    target: type === "cost_spike" ? "" : target,
    magnitude,
  };
  if (type === "supplier_delay") {
    return { delay: magnitude, demand_band_pct: demandBand, scenario };
  }
  if (type === "customer_delay") {
    return { delay: 0, customer_late_days: magnitude, demand_band_pct: demandBand, scenario };
  }
  return { delay: 0, cost_spike_pct: magnitude, demand_band_pct: demandBand, scenario };
}

function isAbort(e: unknown) {
  return e instanceof DOMException && e.name === "AbortError";
}

export default function FireDrill() {
  const [type, setType] = useState<ScenarioType>("supplier_delay");
  const [target, setTarget] = useState("A");
  const [magnitude, setMagnitude] = useState(14);
  const [demandBand, setDemandBand] = useState(20);

  const [result, setResult] = useState<CascadeResult | null>(null);
  const [simLoading, setSimLoading] = useState(true);
  const [simError, setSimError] = useState<unknown>(null);

  const [actions, setActions] = useState<ActionsCompareResponse | null>(null);
  const [actionsLoading, setActionsLoading] = useState(true);
  const [actionsError, setActionsError] = useState<unknown>(null);

  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [selectedEventIds, setSelectedEventIds] = useState<string[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  // Prefill target from /fire-drill?target=... (vendor check deep link).
  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get("target");
    if (t) setTarget(t);
  }, []);

  const run = useCallback(
    async (t: ScenarioType, tg: string, mag: number, band: number) => {
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      setSimLoading(true);
      setSimError(null);
      try {
        const res = await simulateCascade(buildRequest(t, tg, mag, band), ctrl.signal);
        setResult(res);
        setSimLoading(false);
      } catch (e) {
        if (!isAbort(e)) {
          setSimError(e);
          setSimLoading(false);
        }
        return;
      }
      // The compare endpoint models the Supplier-A delay case only.
      if (t === "supplier_delay") {
        setActionsLoading(true);
        setActionsError(null);
        try {
          const acts = await compareActions(mag, ctrl.signal);
          setActions(acts);
        } catch (e) {
          if (!isAbort(e)) setActionsError(e);
        } finally {
          if (!ctrl.signal.aborted) setActionsLoading(false);
        }
      } else {
        setActions(null);
        setActionsLoading(false);
        setActionsError(null);
      }
    },
    [],
  );

  // Auto-run on any control change, debounced so sliders feel live.
  useEffect(() => {
    const h = setTimeout(() => run(type, target, magnitude, demandBand), 300);
    return () => clearTimeout(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type, target, magnitude, demandBand]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const selectedStepDay = result?.cascade_chain?.find((s) => s.step === selectedStep)?.day ?? null;
  const highlightEventDays = (result?.events ?? [])
    .filter((ev) => selectedEventIds.includes(ev.id))
    .map((ev) => ev.day)
    .filter((d, i, a) => a.indexOf(d) === i);

  const suggested = actions ? Object.values(actions).find((a) => a.suggested) : undefined;
  const baselineTimeline = actions?.do_nothing?.cash_timeline ?? null;
  const scenarioNote =
    type === "supplier_delay"
      ? `Compared for a ${magnitude}-day Supplier A delay${target && target !== "A" ? ` (${target})` : ""}.`
      : "Action comparison currently models a Supplier-A delay (the endpoint takes a delay only) — set the type to Supplier delay to compare actions.";

  const s = result?.summary;

  return (
    <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
      {/* Left: scenario controls */}
      <aside className="glass h-fit rounded-2xl p-6 lg:sticky lg:top-24">
        <ScenarioControls
          type={type}
          target={target}
          magnitude={magnitude}
          demandBand={demandBand}
          onChange={(patch) => {
            if (patch.type !== undefined) setType(patch.type);
            if (patch.target !== undefined) setTarget(patch.target);
            if (patch.magnitude !== undefined) setMagnitude(patch.magnitude);
            if (patch.demandBand !== undefined) setDemandBand(patch.demandBand);
            setSelectedStep(null);
            setSelectedEventIds([]);
          }}
          onApplyParsed={(t, tg, mag) => {
            setType(t);
            setTarget(tg);
            setMagnitude(mag);
          }}
        />
      </aside>

      {/* Right: results */}
      <div className="flex min-w-0 flex-col gap-6">
        {/* Headline summary */}
        {simLoading && !result && <LoadingSkeleton rows={2} className="h-24" />}
        {simError ? (
          <ErrorState
            error={simError}
            title="The simulation could not run"
            onRetry={() => run(type, target, magnitude, demandBand)}
          />
        ) : null}
        {result && s && (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            {[
              { label: "Stock-out", value: formatDay(s.stockout_day) },
              { label: "Lost walk-in sales", value: formatInr(s.lost_sales_inr) },
              { label: "Cash below zero", value: formatDay(s.first_negative_day) },
              { label: "Lowest cash", value: formatInr(s.lowest_cash_inr) },
              { label: "Failed payments", value: formatCount(s.failed_payments_count) },
            ].map((m) => (
              <div key={m.label} className="glass rounded-2xl p-4">
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">{m.label}</p>
                <p className="mt-1 font-mono text-lg font-bold text-zinc-100">{m.value}</p>
              </div>
            ))}
            <div className="col-span-2 flex items-center gap-2 md:col-span-5">
              <EstimateBadge />
              <span className="text-xs text-zinc-500">
                All figures are estimates from the simulation on synthetic demo data — the tool suggests; the owner decides.
              </span>
            </div>
          </div>
        )}

        {/* Cascade map */}
        <div className="glass rounded-2xl p-4">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-zinc-400">
            How the problem cascades
          </h3>
          {simLoading && !result ? (
            <LoadingSkeleton rows={2} className="h-40" />
          ) : result?.cascade_chain?.length ? (
            <CascadeMap chain={result.cascade_chain} selectedStep={selectedStep} onSelectStep={setSelectedStep} />
          ) : result ? (
            <p className="py-6 text-center text-sm text-zinc-500">No cascade chain returned for this scenario.</p>
          ) : null}
          {selectedStepDay !== null && (
            <p className="mt-2 text-xs text-primary">
              Selected step is marked on the cash chart at day {selectedStepDay}.
            </p>
          )}
        </div>

        {/* Timelines */}
        {result && (
          <div className="glass rounded-2xl p-6">
            <TimelinesChart
              result={result}
              baseline={baselineTimeline}
              actionTimeline={suggested?.cash_timeline ?? null}
              actionLabel={suggested ? `${suggested.label} (suggested)` : undefined}
              selectedDay={selectedStepDay}
              highlightEventDays={highlightEventDays}
            />
          </div>
        )}

        {/* Ranges */}
        {result?.ranges && (
          <div className="glass rounded-2xl p-6">
            <RangesPanel ranges={result.ranges} />
          </div>
        )}

        {/* Why + events + assumptions */}
        {result?.explanations && (
          <div className="glass rounded-2xl p-6">
            <WhyPanel
              explanations={result.explanations}
              events={result.events ?? []}
              selectedEventIds={selectedEventIds}
              onSelectEvents={setSelectedEventIds}
            />
          </div>
        )}
        {result?.assumptions && (
          <div className="glass rounded-2xl p-6">
            <AssumptionsBox assumptions={result.assumptions} />
          </div>
        )}

        {/* Actions */}
        <div className="glass rounded-2xl p-6">
          {actionsLoading && !actions ? (
            <LoadingSkeleton rows={4} className="h-28" />
          ) : (
            <ActionsCompare
              actions={actions}
              error={actionsError}
              onRetry={() => run(type, target, magnitude, demandBand)}
              scenarioNote={type === "supplier_delay" ? null : scenarioNote}
            />
          )}
        </div>
      </div>
    </div>
  );
}
