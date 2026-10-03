"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, ChevronRight, XCircle } from "lucide-react";
import type { CascadeStep } from "@/lib/types";

const STATUS_CONFIG: Record<
  string,
  { border: string; bg: string; text: string; badge: string; icon: React.ReactNode }
> = {
  triggered: {
    border: "border-red-500/50 hover:border-red-500",
    bg: "bg-red-500/10",
    text: "text-red-500",
    badge: "bg-red-500/20 text-red-400 border-red-500/30",
    icon: <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />,
  },
  avoided: {
    border: "border-green-500/50 hover:border-green-500",
    bg: "bg-green-500/10",
    text: "text-green-500",
    badge: "bg-green-500/20 text-green-400 border-green-500/30",
    icon: <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />,
  },
  not_reached: {
    border: "border-card-border hover:border-muted-foreground",
    bg: "bg-muted/30",
    text: "text-muted-foreground",
    badge: "bg-muted text-muted-foreground border-card-border",
    icon: <XCircle className="w-4 h-4 text-muted-foreground shrink-0" />,
  },
};

export default function CascadeMap({
  chain,
  selectedStep,
  onSelectStep,
}: {
  chain: CascadeStep[];
  selectedStep: string | null;
  onSelectStep: (step: string | null) => void;
}) {
  const [activeStepModal, setActiveStepModal] = useState<CascadeStep | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
          Cascade Milestone Timeline ({chain.length} Nodes)
        </h3>
        <span className="text-[11px] text-muted-foreground">Click card for expanded details</span>
      </div>

      {/* Horizontal Scrollable Domino Chain Container */}
      <div className="overflow-x-auto pb-4 pt-2 -mx-2 px-2 scrollbar-thin">
        <div className="flex items-center gap-4 min-w-max">
          {chain.map((step, i) => {
            const config = STATUS_CONFIG[step.status] ?? STATUS_CONFIG.not_reached;
            const isSelected = selectedStep === step.step;

            return (
              <div key={step.step} className="flex items-center gap-4">
                {/* Domino Timeline Card */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9, y: 15 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{ delay: i * 0.1, duration: 0.35 }}
                  onClick={() => {
                    onSelectStep(isSelected ? null : step.step);
                    setActiveStepModal(step);
                  }}
                  className={`w-[230px] rounded-2xl border p-4 backdrop-blur-md cursor-pointer transition-all shadow-md ${
                    config.bg
                  } ${config.border} ${isSelected ? "ring-2 ring-primary scale-[1.03]" : ""}`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase ${config.badge}`}>
                      {config.icon}
                      {step.status.replace("_", " ")}
                    </span>
                    {step.day !== null && (
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-md bg-card border border-card-border text-foreground">
                        Day {step.day}
                      </span>
                    )}
                  </div>

                  <h4 className="font-bold text-sm text-foreground line-clamp-1">{step.title}</h4>
                  <p className="text-xs text-muted-foreground line-clamp-3 mt-1 leading-snug">{step.detail}</p>
                </motion.div>

                {/* Animated Flow Connector */}
                {i < chain.length - 1 && (
                  <div className="relative flex items-center justify-center w-8">
                    <div className="h-0.5 w-full bg-card-border" />
                    <motion.div
                      animate={{ x: [0, 16, 0] }}
                      transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
                      className="absolute"
                    >
                      <ChevronRight className="w-4 h-4 text-primary" />
                    </motion.div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Expanded Modal / Detail Callout */}
      {activeStepModal && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-primary/30 bg-primary/10 p-4 space-y-2 text-left"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-primary uppercase">Node Details: {activeStepModal.title}</span>
            <button
              onClick={() => setActiveStepModal(null)}
              className="text-xs font-bold text-muted-foreground hover:text-foreground"
            >
              Close ✕
            </button>
          </div>
          <p className="text-xs text-foreground leading-relaxed">{activeStepModal.detail}</p>
          {activeStepModal.day !== null && (
            <p className="font-mono text-xs font-bold text-primary font-tabular">
              Triggered on Simulation Day {activeStepModal.day}
            </p>
          )}
        </motion.div>
      )}
    </div>
  );
}
