"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Handle,
  Position,
  ReactFlow,
  Node,
  NodeProps,
  Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { motion, useReducedMotion } from "framer-motion";
import type { CascadeStep } from "@/lib/types";

/**
 * Cascade map drawn from the API's `cascade_chain` (six steps). Node styling
 * reflects `status` (triggered / avoided / not_reached); status text is always
 * shown beside the colour. Clicking a node selects that step (day highlight).
 */

const STATUS_STYLES: Record<string, { border: string; text: string; dot: string }> = {
  triggered: { border: "border-red-500/50 bg-red-500/10", text: "text-red-400", dot: "#EF4444" },
  avoided: { border: "border-green-500/50 bg-green-500/10", text: "text-green-400", dot: "#22C55E" },
  not_reached: { border: "border-white/10 bg-white/5", text: "text-zinc-500", dot: "#71717A" },
};

export type ChainNodeData = {
  index: number;
  step: CascadeStep;
  selected: boolean;
  onSelect: (step: string | null) => void;
};

function ChainNode({ data }: NodeProps) {
  const d = data as unknown as ChainNodeData;
  const reduce = useReducedMotion();
  const s = STATUS_STYLES[d.step.status] ?? STATUS_STYLES.not_reached;
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: reduce ? 0 : d.index * 0.12, duration: 0.3 }}
      className={`h-full w-full cursor-pointer rounded-xl border p-3 backdrop-blur-sm transition-shadow ${s.border} ${
        d.selected ? "ring-2 ring-primary" : ""
      }`}
      onClick={() => d.onSelect(d.selected ? null : d.step.step)}
      role="button"
      aria-pressed={d.selected}
      aria-label={`${d.step.title}, ${d.step.status}, ${d.step.day !== null ? `day ${d.step.day}` : "no day"}`}
    >
      <Handle type="target" position={Position.Left} className="!opacity-0" />
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-zinc-100">{d.step.title}</span>
        {d.step.day !== null && (
          <span className="rounded-full bg-black/30 px-1.5 py-0.5 font-mono text-[10px] text-zinc-300">
            d{d.step.day}
          </span>
        )}
      </div>
      <p className={`mt-1 text-[10px] font-bold uppercase tracking-wide ${s.text}`}>
        {d.step.status.replace("_", " ")}
      </p>
      <p className="mt-1 line-clamp-3 text-[10px] leading-snug text-zinc-400">{d.step.detail}</p>
      <Handle type="source" position={Position.Right} className="!opacity-0" />
    </motion.div>
  );
}

const nodeTypes = { chain: ChainNode };

export default function CascadeMap({
  chain,
  selectedStep,
  onSelectStep,
}: {
  chain: CascadeStep[];
  selectedStep: string | null;
  onSelectStep: (step: string | null) => void;
}) {
  // On narrow screens lay the chain out in two columns so it fits a 360px
  // phone without horizontal scroll; on wide screens a single row.
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 640px)");
    const update = () => setNarrow(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  const nodes: Node[] = useMemo(
    () =>
      chain.map((step, i) => ({
        id: step.step,
        type: "chain",
        position: narrow
          ? { x: (i % 2) * 240, y: Math.floor(i / 2) * 165 }
          : { x: i * 250, y: 0 },
        data: { index: i, step, selected: selectedStep === step.step, onSelect: onSelectStep },
        draggable: false,
        selectable: true,
      })),
    [chain, selectedStep, onSelectStep, narrow],
  );

  const edges: Edge[] = useMemo(
    () =>
      chain.slice(1).map((step, i) => ({
        id: `${chain[i].step}-${step.step}`,
        source: chain[i].step,
        target: step.step,
        style: { stroke: "rgba(255,255,255,0.18)", strokeWidth: 2 },
      })),
    [chain],
  );

  return (
    <div className="h-[280px] w-full" aria-label="Cascade chain map" role="img">
      <ReactFlow
        key={narrow ? "narrow" : "wide"}
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.12 }}
        minZoom={0.2}
        nodesDraggable={false}
        nodesConnectable={false}
        proOptions={{ hideAttribution: true }}
        onPaneClick={() => onSelectStep(null)}
      >
        <Background color="#0A0A0F" gap={20} />
      </ReactFlow>
    </div>
  );
}
