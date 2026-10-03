/**
 * Display-only formatters. The frontend never computes business figures —
 * these functions only format numbers that came from the API.
 */

/** Indian-grouped rupees: 177600 → ₹1,77,600 and -171600 → ₹-1,71,600. */
export function formatInr(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const abs = Math.abs(value);
  const grouped = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(abs);
  return value < 0 ? `₹-${grouped}` : `₹${grouped}`;
}

/** Day 23, or an em dash when the engine returned null. */
export function formatDay(day: number | null | undefined): string {
  if (day === null || day === undefined) return "—";
  return `Day ${day}`;
}

/** Plain count with an em dash for null. */
export function formatCount(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return String(value);
}

/** Percentages: 27.54 → "27.54%", 10 → "10%". */
export function formatPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(value)}%`;
}

/** Risk level → colour classes + label. Text is always shown beside colour. */
export const RISK_STYLES: Record<string, { chip: string; text: string; bar: string }> = {
  Low: { chip: "bg-green-500/15 text-green-400 border-green-500/30", text: "text-green-400", bar: "#22C55E" },
  Medium: { chip: "bg-amber-500/15 text-amber-400 border-amber-500/30", text: "text-amber-400", bar: "#F59E0B" },
  High: { chip: "bg-red-500/15 text-red-400 border-red-500/30", text: "text-red-400", bar: "#EF4444" },
};

export function riskStyle(level: string) {
  return RISK_STYLES[level] ?? RISK_STYLES.Medium;
}

/** safe / watch / critical (stock cover) → colour classes. */
export const STATUS_STYLES: Record<string, string> = {
  safe: "bg-green-500/15 text-green-400 border-green-500/30",
  watch: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
};

/** high / medium / low concentration chips. */
export const CONCENTRATION_STYLES: Record<string, string> = {
  high: "bg-red-500/15 text-red-400 border-red-500/30",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  low: "bg-green-500/15 text-green-400 border-green-500/30",
};

/** Assumption source → label. */
export const SOURCE_LABELS: Record<string, string> = {
  demo_data: "demo data",
  assumed: "assumption",
  user: "you set",
};

/** Vendor band → colour classes + label. */
export const BAND_STYLES: Record<string, string> = {
  green: "bg-green-500/15 text-green-400 border-green-500/30",
  amber: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  red: "bg-red-500/15 text-red-400 border-red-500/30",
  unknown: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
};
