"use client";
import { useState } from 'react';
import { checkVendor } from '@/lib/api';
import { Search, CheckCircle, AlertTriangle } from 'lucide-react';

interface VendorResult {
  score: number;
  badge: string;
  reasons: string[];
}

export default function VendorCheck() {
  const [query, setQuery] = useState('New Distributor');
  const [result, setResult] = useState<VendorResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCheck = async () => {
    setLoading(true);
    try {
      const res = await checkVendor({ name: query });
      setResult(res);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const SAMPLES = ['New Distributor', 'Supplier A', 'Supplier C'];

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">Vendor Trust Check</h1>
        <p className="text-zinc-400">Verify a vendor&apos;s history before adding them to a scenario.</p>
      </div>

      <div className="glass p-2 rounded-full flex items-center gap-2 max-w-xl mx-auto border border-white/10">
        <div className="pl-4 text-zinc-400"><Search className="w-5 h-5" /></div>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleCheck()}
          placeholder="Enter GSTIN, PAN, or Company Name"
          className="flex-1 bg-transparent border-none outline-none text-white px-2 py-3"
        />
        <button onClick={handleCheck} disabled={loading} className="px-6 py-2.5 rounded-full bg-primary text-white font-medium hover:bg-primary/90 transition disabled:opacity-50">
          {loading ? 'Checking...' : 'Check'}
        </button>
      </div>

      <div className="flex justify-center gap-3">
        {SAMPLES.map(s => (
          <button key={s} onClick={() => setQuery(s)} className="text-xs px-4 py-2 rounded-full glass border border-white/10 hover:border-primary/50 transition">
            {s}
          </button>
        ))}
      </div>

      {result && (
        <div className="glass p-8 rounded-3xl flex flex-col md:flex-row gap-8 items-center border border-white/10">
          <div className="flex-shrink-0 relative flex items-center justify-center w-40 h-40">
            <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 160 160">
              <circle cx="80" cy="80" r="68" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
              <circle cx="80" cy="80" r="68" fill="none"
                stroke={result.badge === 'red' ? '#EF4444' : result.badge === 'amber' ? '#F59E0B' : '#22C55E'}
                strokeWidth="10"
                strokeDasharray={`${427 * result.score / 100} 427`}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className={`text-5xl font-black font-mono ${result.badge === 'red' ? 'text-red-400' : result.badge === 'amber' ? 'text-amber-400' : 'text-green-400'}`}>
              {result.score}
            </div>
          </div>

          <div className="flex-1 space-y-4 w-full">
            <div className="flex items-center gap-3">
              <h3 className="text-xl font-bold">{query}</h3>
              <span className={`text-xs font-bold px-3 py-1 rounded-full uppercase ${
                result.badge === 'red' ? 'bg-red-500/20 text-red-400' :
                result.badge === 'amber' ? 'bg-amber-500/20 text-amber-400' :
                'bg-green-500/20 text-green-400'
              }`}>{result.badge} risk</span>
            </div>
            <div className="space-y-2">
              {result.reasons.map((reason: string, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/5">
                  {result.badge !== 'green' ? <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" /> : <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />}
                  <span className="text-sm text-zinc-300">{reason}</span>
                </div>
              ))}
            </div>
            <button className="mt-4 w-full py-2.5 rounded-xl border border-primary/50 text-primary text-sm font-medium hover:bg-primary/10 transition">
              Use this vendor in a Fire Drill
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
