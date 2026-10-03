"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { checkVendor } from "@/lib/api";
import { Search, ShieldCheck, Building2, FileText, Scale, Info, AlertTriangle, ArrowRight, ShieldAlert } from "lucide-react";
import { ErrorState, EmptyState } from "@/components/ui/states";
import { GlassCard } from "@/components/ui/GlassCard";

interface EvidenceItem {
  type: string;
  status: "pass" | "warn" | "fail" | "info";
  detail: string;
}

interface VendorDetails {
  age_years: number;
  address: string;
  state: string;
  court_cases_count: number;
  missing_filings_count: number;
  adverse_media_count: number;
}

interface VendorResult {
  name: string;
  score: number;
  badge: string;
  risk_level: string;
  gstin: string;
  pan: string;
  reasons: string[];
  evidence: EvidenceItem[];
  details: VendorDetails;
  is_mock: boolean;
}

const EVIDENCE_ICONS: Record<string, React.ReactNode> = {
  gstin: <ShieldCheck className="w-4 h-4 shrink-0" />,
  pan: <ShieldCheck className="w-4 h-4 shrink-0" />,
  age: <Building2 className="w-4 h-4 shrink-0" />,
  filings: <FileText className="w-4 h-4 shrink-0" />,
  legal: <Scale className="w-4 h-4 shrink-0" />,
  insolvency: <Scale className="w-4 h-4 shrink-0" />,
  governance: <Info className="w-4 h-4 shrink-0" />,
  premises: <Building2 className="w-4 h-4 shrink-0" />,
  adverse_media: <AlertTriangle className="w-4 h-4 shrink-0" />,
};

const STATUS_COLORS = {
  pass: "text-green-500 bg-green-500/10 border-green-500/30",
  warn: "text-amber-500 bg-amber-500/10 border-amber-500/30",
  fail: "text-red-500 bg-red-500/10 border-red-500/30",
  info: "text-blue-500 bg-blue-500/10 border-blue-500/30",
};

const BADGE_COLORS = {
  green: { bg: "bg-green-500/15", border: "border-green-500/30", text: "text-green-500", stroke: "#22C55E" },
  amber: { bg: "bg-amber-500/15", border: "border-amber-500/30", text: "text-amber-500", stroke: "#F59E0B" },
  red: { bg: "bg-red-500/15", border: "border-red-500/30", text: "text-red-500", stroke: "#EF4444" },
};

const SAMPLES = ["New Distributor", "Supplier A", "Supplier C", "Shree Balaji Components", "Zenith Circuit Importers"];

export default function VendorCheck() {
  const [query, setQuery] = useState("New Distributor");
  const [result, setResult] = useState<VendorResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const handleCheck = async (nameToQuery = query) => {
    if (!nameToQuery.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await checkVendor({ name: nameToQuery });
      setResult(res);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  };

  const badge = result ? BADGE_COLORS[result.badge as keyof typeof BADGE_COLORS] ?? BADGE_COLORS.amber : null;

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
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">Vendor Trust Check</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Verify regulatory signals, GSTIN checksums, and legal risk score before adding suppliers to scenario models.
          </p>
        </div>
        <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-amber-500">
          Mock data — labeled
        </span>
      </div>

      {/* Search Bar */}
      <GlassCard className="p-3">
        <div className="flex items-center gap-3">
          <Search className="w-5 h-5 text-muted-foreground ml-2 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCheck()}
            placeholder="Enter vendor name, GSTIN (e.g. 27AAAAA0000A1Z5), or PAN"
            className="flex-1 bg-transparent border-none outline-none text-foreground text-sm placeholder:text-muted-foreground"
          />
          <button
            onClick={() => handleCheck()}
            disabled={loading}
            className="px-6 py-2.5 rounded-xl bg-primary text-white font-bold text-xs shadow-md hover:bg-primary/90 transition-all disabled:opacity-50 shrink-0"
          >
            {loading ? "Evaluating..." : "Audit Vendor"}
          </button>
        </div>
      </GlassCard>

      {/* Sample Pills */}
      <div className="flex flex-wrap items-center justify-center gap-2">
        <span className="text-xs text-muted-foreground font-medium mr-1">Quick Sample Presets:</span>
        {SAMPLES.map((s) => (
          <button
            key={s}
            onClick={() => {
              setQuery(s);
              handleCheck(s);
            }}
            className="text-xs font-semibold px-3 py-1.5 rounded-full border border-card-border bg-card/60 hover:bg-muted text-muted-foreground hover:text-foreground transition-all"
          >
            {s}
          </button>
        ))}
      </div>

      {error ? <ErrorState error={error} title="The vendor check could not run" onRetry={() => handleCheck()} /> : null}

      {/* Placeholder before first search */}
      {!result && !loading && !error && (
        <EmptyState title="Search or click a preset vendor above to perform due diligence" />
      )}

      {/* Result Card */}
      {result && badge && (
        <GlassCard className="space-y-6">
          {/* Header & Circular Score Gauge */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 border-b border-card-border pb-6">
            <div className="flex items-center gap-6">
              {/* Radial Score Gauge */}
              <div className="relative flex items-center justify-center w-28 h-28 shrink-0">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="50" fill="none" stroke="var(--card-border)" strokeWidth="10" />
                  <circle
                    cx="60"
                    cy="60"
                    r="50"
                    fill="none"
                    stroke={badge.stroke}
                    strokeWidth="10"
                    strokeDasharray="314"
                    strokeDashoffset={314 - (314 * result.score) / 100}
                    strokeLinecap="round"
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute flex flex-col items-center">
                  <span className="font-mono text-2xl font-black text-foreground font-tabular">{result.score}</span>
                  <span className="text-[10px] text-muted-foreground uppercase font-bold">/ 100</span>
                </div>
              </div>

              <div>
                <h2 className="text-xl font-bold text-foreground">{result.name}</h2>
                <p className="text-xs text-muted-foreground mt-0.5 font-mono font-tabular">
                  GSTIN: {result.gstin} · PAN: {result.pan}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`px-3 py-1 rounded-full border text-xs font-bold capitalize ${badge.bg} ${badge.border} ${badge.text}`}>
                    {result.badge} Band ({result.risk_level} Risk)
                  </span>
                </div>
              </div>
            </div>

            {/* Deep-link Action Button */}
            <Link
              href={`/fire-drill?target=${encodeURIComponent(result.name)}`}
              className="px-6 py-3 rounded-2xl bg-primary text-white font-bold text-xs shadow-lg shadow-primary/25 hover:bg-primary/90 transition-all flex items-center gap-2 shrink-0"
            >
              Use This Vendor in Fire Drill <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Red Flag Summary */}
          {result.reasons && result.reasons.length > 0 && (
            <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-red-500 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4" /> Risk Reasons Flagged
              </h3>
              <ul className="list-disc pl-5 text-xs text-foreground space-y-1">
                {result.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 8 Signals Grid */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Regulatory & Compliance Evidence</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.evidence.map((item, idx) => {
                const statusCls = STATUS_COLORS[item.status] ?? STATUS_COLORS.info;
                const icon = EVIDENCE_ICONS[item.type] ?? <Info className="w-4 h-4" />;

                return (
                  <div key={idx} className="flex items-start gap-3 rounded-xl border border-card-border bg-muted/40 p-3.5">
                    <div className={`p-2 rounded-lg border ${statusCls} shrink-0`}>{icon}</div>
                    <div>
                      <span className="text-xs font-bold text-foreground capitalize">{item.type.replace(/_/g, " ")}</span>
                      <p className="text-xs text-muted-foreground mt-0.5 leading-snug">{item.detail}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </GlassCard>
      )}
    </motion.div>
  );
}
