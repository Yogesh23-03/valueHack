"use client";

import { useMemo } from "react";
import { Activity } from "lucide-react";
import type { Explanation, SimEvent } from "@/lib/types";
import { formatCount, formatDay, formatInr } from "@/lib/format";
import { EmptyState } from "@/components/ui/states";

/**
 * "Why?" panel: the engine's explanation sentences (one per metric) and the
 * dated event timeline. Clicking an explanation highlights its event_ids;
 * colour for severity is always paired with text.
 */

const SEVERITY_STYLES: Record<string, { chip: string; label: string }> = {
  critical: { chip: "bg-red-500/15 text-red-400 border-red-500/30", label: "critical" },
  warning: { chip: "bg-amber-500/15 text-amber-400 border-amber-500/30", label: "warning" },
  info: { chip: "bg-white/10 text-zinc-400 border-white/10", label: "info" },
};

function formatValue(unit: string, value: number | null): string {
  if (value === null) return "";
  if (unit === "inr") return formatInr(value);
  if (unit === "day") return formatDay(value);
  return formatCount(value);
}

export default function WhyPanel({
  explanations,
  events,
  selectedEventIds,
  onSelectEvents,
}: {
  explanations: Explanation[];
  events: SimEvent[];
  selectedEventIds: string[];
  onSelectEvents: (ids: string[]) => void;
}) {
  const selected = useMemo(() => new Set(selectedEventIds), [selectedEventIds]);

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-400">Why? — engine explanations</h3>
        {explanations.length === 0 ? (
          <EmptyState title="No explanations for this run" icon={<Activity className="h-5 w-5" />} />
        ) : (
          <ul className="space-y-2.5">
            {explanations.map((ex) => {
              const linked = ex.event_ids.length > 0;
              return (
                <li key={ex.metric_id}>
                  <button
                    type="button"
                    disabled={!linked}
                    onClick={() => onSelectEvents(linked ? ex.event_ids : [])}
                    className={`w-full rounded-xl border border-white/5 bg-white/5 p-3 text-left transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary ${
                      linked ? "hover:border-primary/40" : "cursor-default"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-primary">{ex.label}</span>
                      {ex.value !== null && (
                        <span className="rounded-full bg-primary/10 px-2 py-0.5 font-mono text-[10px] text-primary">
                          {formatValue(ex.unit, ex.value)}
                        </span>
                      )}
                    </span>
                    <p className="mt-1 text-sm leading-snug text-zinc-300">{ex.sentence}</p>
                    {linked && (
                      <p className="mt-1 text-[10px] text-zinc-500">
                        {selectedEventIds.length > 0 && ex.event_ids.every((id) => selected.has(id))
                          ? "Click to clear event highlight"
                          : "Click to highlight the related events →"}
                      </p>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-400">
          What happened, day by day
        </h3>
        {events.length === 0 ? (
          <EmptyState title="No events in this run" />
        ) : (
          <ol className="max-h-80 space-y-2 overflow-y-auto pr-1">
            {events.map((ev) => {
              const sev = SEVERITY_STYLES[ev.severity] ?? SEVERITY_STYLES.info;
              const isSel = selected.has(ev.id);
              return (
                <li
                  key={ev.id}
                  className={`rounded-xl border p-3 transition ${
                    isSel ? "border-amber-500/60 bg-amber-500/10" : "border-white/5 bg-white/5"
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-[10px] text-zinc-500">{ev.id}</span>
                    <span className="text-xs font-semibold text-zinc-200">{formatDay(ev.day)}</span>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase ${sev.chip}`}>
                      {sev.label}
                    </span>
                    <span className="text-xs text-zinc-400">{ev.type.replace(/_/g, " ")} — {ev.entity}</span>
                  </div>
                  {Object.keys(ev.values).length > 0 && (
                    <p className="mt-1 font-mono text-[10px] text-zinc-500">
                      {Object.entries(ev.values)
                        .map(([k, v]) => `${k}=${String(v)}`)
                        .join(", ")}
                    </p>
                  )}
                </li>
              );
            })}
          </ol>
        )}
      </div>
    </div>
  );
}
