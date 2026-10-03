import { Info } from "lucide-react";
import { BAND_STYLES, CONCENTRATION_STYLES, RISK_STYLES, SOURCE_LABELS, STATUS_STYLES, riskStyle } from "@/lib/format";

/** Small chip shown next to any figure that is an estimate. */
export function EstimateBadge({ className = "" }: { className?: string }) {
  return (
    <span
      title="Value from the simulation — an estimate, not a prediction"
      className={`inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-primary ${className}`}
    >
      <Info className="h-3 w-3" aria-hidden />
      Estimate
    </span>
  );
}

/** Low / Medium / High risk badge — colour always paired with text. */
export function RiskBadge({ level, className = "" }: { level: string; className?: string }) {
  const s = riskStyle(level);
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${s.chip} ${className}`}>
      {level} risk
    </span>
  );
}

/** safe / watch / critical chip for stock cover rows. */
export function StatusChip({ status }: { status: string }) {
  const cls = STATUS_STYLES[status] ?? STATUS_STYLES.watch;
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cls}`}>
      {status}
    </span>
  );
}

/** high / medium / low supplier concentration chip. */
export function ConcentrationChip({ level }: { level: string }) {
  const cls = CONCENTRATION_STYLES[level] ?? CONCENTRATION_STYLES.low;
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cls}`}>
      {level} concentration
    </span>
  );
}

/** Assumption source tag: demo data / assumption / you set. */
export function SourceTag({ source }: { source: string }) {
  return (
    <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-medium text-zinc-400">
      {SOURCE_LABELS[source] ?? source}
    </span>
  );
}

/** Vendor trust band badge: green / amber / red / unknown. */
export function BandBadge({ band }: { band: string }) {
  const cls = BAND_STYLES[band] ?? BAND_STYLES.unknown;
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold capitalize ${cls}`}>
      {band} band
    </span>
  );
}

/** Risk-level colour swatch used in chart legends. */
export function RiskColorDot({ level }: { level: string }) {
  return <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: RISK_STYLES[level]?.bar ?? "#F59E0B" }} aria-hidden />;
}
