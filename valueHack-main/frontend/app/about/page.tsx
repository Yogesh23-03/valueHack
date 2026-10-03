"use client";

import { motion } from "framer-motion";
import { Info, Cpu, AlertTriangle, Layers, Brain, ShieldAlert } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";

const ENGINE_MODULES = [
  { name: "engine/cascade.py", desc: "Day-by-day deterministic simulation with structured events", icon: <Cpu className="w-4 h-4 text-primary" /> },
  { name: "engine/actions.py", desc: "6 response strategies with affordability, risk rubric and suggestion", icon: <Layers className="w-4 h-4 text-primary" /> },
  { name: "engine/pricing.py", desc: "Price what-if with elasticity bands and break-even demand drop", icon: <Brain className="w-4 h-4 text-primary" /> },
  { name: "engine/analytics.py", desc: "Supplier dependency shares and stock cover days", icon: <Info className="w-4 h-4 text-primary" /> },
  { name: "engine/ranges.py", desc: "Demand low/base/high scenario reruns", icon: <Cpu className="w-4 h-4 text-primary" /> },
  { name: "engine/models.py", desc: "Data-driven Business, Product, Customer and Shock models", icon: <Layers className="w-4 h-4 text-primary" /> },
  { name: "engine/adapters.py", desc: "Builds the Business model from dict or database", icon: <Cpu className="w-4 h-4 text-primary" /> },
  { name: "explain/reasons.py", desc: "Plain-language explanations, cascade chain and assumptions", icon: <Info className="w-4 h-4 text-primary" /> },
  { name: "signals/vendor.py", desc: "Rule-based trust scoring (8 mock GSTIN/legal signals)", icon: <ShieldAlert className="w-4 h-4 text-primary" /> },
  { name: "signals/llm.py", desc: "Regex scenario parser for disruption text", icon: <Brain className="w-4 h-4 text-primary" /> },
];

export default function About() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-4xl mx-auto space-y-8"
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-card-border pb-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">Model Card & Assumptions</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Engine architecture, simulation boundaries, and transparency notes for SMVIT ValueHack 2026.
          </p>
        </div>
      </div>

      <GlassCard className="p-8 space-y-8 text-foreground">
        {/* Disclaimer Callout */}
        <div className="rounded-2xl border border-primary/30 bg-primary/10 p-5 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-primary uppercase tracking-wider">
            <Info className="w-4 h-4" /> Disclaimer & Scope
          </div>
          <p className="text-xs text-foreground leading-relaxed">
            BizSim is a <strong>deterministic simulation engine</strong> designed to illustrate cash flow risks. It uses <em>synthetic demo data</em> for demonstration purposes. These are estimates from mathematical rules, not financial predictions.
          </p>
        </div>

        {/* How It Works */}
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">Simulation Mechanics</h2>
          <p className="text-xs text-muted-foreground leading-relaxed">
            The engine steps through days 1 to 30. Each day it computes inventory drawdowns, accounts receivable collections, and accounts payable obligations. If cash drops below zero, subsequent payables are marked as failed payments.
          </p>
        </div>

        {/* Engine Modules Grid */}
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">Engine Modules Architecture</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {ENGINE_MODULES.map((m) => (
              <div key={m.name} className="p-4 rounded-xl border border-card-border bg-muted/30 space-y-1">
                <div className="flex items-center gap-2">
                  {m.icon}
                  <code className="text-xs font-mono font-bold text-primary">{m.name}</code>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{m.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Assumptions List */}
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-foreground">Model Assumptions</h2>
          <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-2 leading-relaxed">
            <li>Demand is assumed constant at historical daily averages for the 30-day window.</li>
            <li>Customers pay exactly X days after delivery — no partial payments modeled.</li>
            <li>No external financing (lines of credit, overdrafts) unless explicitly selected in scenario controls.</li>
            <li>Vendor trust scores are entirely rule-based on mock data — not real registry lookups.</li>
            <li>Bill scan uses Gemini Vision; falls back to a structured sample if the API is unavailable.</li>
          </ul>
        </div>

        {/* Limitations Section */}
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-warning" /> Limitations & What We Do NOT Claim
          </h2>
          <ul className="list-disc pl-5 text-xs text-muted-foreground space-y-2 leading-relaxed">
            <li>These figures are <strong>estimates, not predictions</strong>.</li>
            <li>Vendor scores are illustrative — consult official GST/PAN registries before business decisions.</li>
            <li>The scenario parser uses pattern-matching fallbacks and does not provide financial advice.</li>
          </ul>
        </div>

        {/* Footer Quote */}
        <div className="p-4 rounded-2xl border border-card-border bg-muted/40 text-center text-xs font-bold text-primary font-mono tracking-wide">
          &ldquo;The tool suggests; the owner decides.&rdquo;
        </div>
      </GlassCard>
    </motion.div>
  );
}
