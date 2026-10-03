"use client";
import { useState } from 'react';
import Link from 'next/link';
import { checkVendor } from '@/lib/api';
import { Search, CheckCircle, AlertTriangle, XCircle, ShieldCheck, Building2, FileText, Scale, Info } from 'lucide-react';
import { ErrorState } from '@/components/ui/states';

interface EvidenceItem {
  type: string;
  status: 'pass' | 'warn' | 'fail' | 'info';
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
  pass: 'text-green-400',
  warn: 'text-amber-400',
  fail: 'text-red-400',
  info: 'text-blue-400',
};

const BADGE_COLORS = {
  green: { bg: 'bg-green-500/15', border: 'border-green-500/30', text: 'text-green-400', stroke: '#22C55E' },
  amber: { bg: 'bg-amber-500/15', border: 'border-amber-500/30', text: 'text-amber-400', stroke: '#F59E0B' },
  red: { bg: 'bg-red-500/15', border: 'border-red-500/30', text: 'text-red-400', stroke: '#EF4444' },
};

export default function VendorCheck() {
  const [query, setQuery] = useState('New Distributor');
  const [result, setResult] = useState<VendorResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const handleCheck = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await checkVendor({ name: query });
      setResult(res);
    } catch (e) {
      setError(e);
    }
    setLoading(false);
  };

  const SAMPLES = ['New Distributor', 'Supplier A', 'Supplier C', 'Shree Balaji Components', 'Zenith Circuit Importers'];
  const badge = result ? (BADGE_COLORS[result.badge as keyof typeof BADGE_COLORS] ?? BADGE_COLORS.amber) : null;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Vendor Trust Check</h1>
        <p className="text-zinc-400 text-sm">
          Verify a vendor's regulatory signals and legal history before using them in a scenario.
          <span className="ml-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-400">
            Mock data — labeled
          </span>
        </p>
      </div>

      {/* Search bar */}
      <div className="glass p-2 rounded-full flex items-center gap-2 max-w-xl mx-auto border border-white/10">
        <div className="pl-4 text-zinc-400"><Search className="w-5 h-5" /></div>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleCheck()}
          placeholder="Enter GSTIN, PAN, or company name"
          className="flex-1 bg-transparent border-none outline-none text-white px-2 py-3 text-sm"
        />
        <button
          id="vendor-check-btn"
          onClick={handleCheck}
          disabled={loading}
          className="px-6 py-2.5 rounded-full bg-primary text-white font-medium hover:bg-primary/90 transition disabled:opacity-50 text-sm"
        >
          {loading ? 'Checking...' : 'Check'}
        </button>
      </div>

      {/* Quick samples */}
      <div className="flex flex-wrap justify-center gap-2">
        {SAMPLES.map(s => (
          <button
            key={s}
            onClick={() => { setQuery(s); }}
            className="text-xs px-3 py-1.5 rounded-full glass border border-white/10 hover:border-primary/50 transition"
          >
            {s}
          </button>
        ))}
      </div>

      {error ? <ErrorState error={error} title="The vendor check could not run" onRetry={handleCheck} /> : null}

      {/* Result card */}
      {result && badge && (
        <div className={`glass rounded-3xl border ${badge.border} overflow-hidden`}>
          {/* Score header */}
          <div className={`${badge.bg} px-8 py-6 flex flex-col md:flex-row gap-6 items-center`}>
            {/* Circular score gauge */}
            <div className="relative flex-shrink-0 flex items-center justify-center w-36 h-36">
              <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 160 160">
                <circle cx="80" cy="80" r="68" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
                <circle cx="80" cy="80" r="68" fill="none"
                  stroke={badge.stroke}
                  strokeWidth="10"
                  strokeDasharray={`${427 * result.score / 100} 427`}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className={`text-5xl font-black font-mono ${badge.text}`}>{result.score}</div>
            </div>

            {/* Name, badge, GSTIN/PAN, details */}
            <div className="flex-1 space-y-2 text-left">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-xl font-bold">{result.name}</h2>
                <span className={`text-xs font-bold px-3 py-1 rounded-full uppercase ${badge.bg} ${badge.text} border ${badge.border}`}>
                  {result.risk_level} Risk
                </span>
                {result.is_mock && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full border border-zinc-600 text-zinc-500 uppercase">Mock</span>
                )}
              </div>
              <div className="flex flex-wrap gap-4 text-xs text-zinc-400">
                {result.gstin && <span><span className="text-zinc-500">GSTIN</span> {result.gstin}</span>}
                {result.pan && <span><span className="text-zinc-500">PAN</span> {result.pan}</span>}
                {result.details?.state && <span><span className="text-zinc-500">State</span> {result.details.state}</span>}
              </div>
              {result.details && (
                <div className="flex flex-wrap gap-4 text-xs">
                  <span className="text-zinc-400">
                    Age: <span className="text-white font-medium">{result.details.age_years.toFixed(1)}y</span>
                  </span>
                  <span className="text-zinc-400">
                    Court cases: <span className={result.details.court_cases_count > 0 ? 'text-red-400 font-medium' : 'text-green-400 font-medium'}>{result.details.court_cases_count}</span>
                  </span>
                  <span className="text-zinc-400">
                    Missing filings: <span className={result.details.missing_filings_count > 0 ? 'text-amber-400 font-medium' : 'text-green-400 font-medium'}>{result.details.missing_filings_count}</span>
                  </span>
                  <span className="text-zinc-400">
                    Adverse media: <span className={result.details.adverse_media_count > 0 ? 'text-red-400 font-medium' : 'text-green-400 font-medium'}>{result.details.adverse_media_count}</span>
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Evidence items */}
          <div className="px-8 py-6 space-y-2">
            <h3 className="text-sm font-semibold text-zinc-300 mb-3">Verification Evidence</h3>
            {result.evidence.map((ev, i) => (
              <div key={i} className={`flex items-start gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]`}>
                <span className={STATUS_COLORS[ev.status]}>
                  {ev.status === 'pass'
                    ? <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" />
                    : ev.status === 'fail'
                    ? <XCircle className="w-4 h-4 mt-0.5 shrink-0" />
                    : (EVIDENCE_ICONS[ev.type] || <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />)
                  }
                </span>
                <div className="flex-1 min-w-0">
                  <span className="text-xs text-zinc-500 uppercase font-semibold mr-2">{ev.type.replace('_', ' ')}</span>
                  <span className={`text-sm ${STATUS_COLORS[ev.status]}`}>{ev.detail}</span>
                </div>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div className="px-8 pb-6">
            <Link
              href={`/fire-drill?target=${encodeURIComponent(query)}`}
              id="use-vendor-fire-drill-btn"
              className="block w-full rounded-xl border border-primary/50 py-2.5 text-center text-sm font-medium text-primary transition hover:bg-primary/10"
            >
              Use this vendor in a Fire Drill →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
