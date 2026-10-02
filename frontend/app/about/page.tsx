"use client";
export default function About() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold">Model Card &amp; Assumptions</h1>
      <div className="glass p-8 rounded-3xl space-y-6 text-zinc-300 leading-relaxed">
        <p>
          <strong className="text-white">Disclaimer:</strong> BizSim is a deterministic simulation engine designed to illustrate cash flow risks. It uses{' '}
          <em>synthetic data</em> for demonstration purposes.
        </p>

        <h3 className="text-xl font-bold text-white mt-8 mb-4">How it works</h3>
        <p>
          The engine steps through days 1 to 30. Each day it computes inventory drawdowns, accounts receivable collections,
          and accounts payable obligations. If cash drops below zero, subsequent payables are marked as failed.
        </p>

        <h3 className="text-xl font-bold text-white mt-8 mb-4">Engine modules</h3>
        <div className="grid grid-cols-2 gap-3">
          {[
            { name: 'cascade.py', desc: 'Day-by-day deterministic simulation' },
            { name: 'actions.py', desc: '5 pre-defined response strategies' },
            { name: 'forecast.py', desc: 'Seasonal average demand forecast' },
            { name: 'anomaly.py', desc: 'Z-score anomaly detection on sales & cost' },
            { name: 'vendor.py', desc: 'Rule-based trust scoring (mock data)' },
            { name: 'bills.py', desc: 'AI bill extraction via Gemini Vision' },
          ].map(m => (
            <div key={m.name} className="p-3 rounded-xl bg-white/5 border border-white/5">
              <code className="text-primary text-sm font-mono">{m.name}</code>
              <p className="text-xs text-zinc-400 mt-1">{m.desc}</p>
            </div>
          ))}
        </div>

        <h3 className="text-xl font-bold text-white mt-8 mb-4">Assumptions</h3>
        <ul className="list-disc pl-5 space-y-2">
          <li>Demand is assumed constant at historical averages for the 30-day window.</li>
          <li>Customers pay exactly X days after delivery — no partial payments modeled.</li>
          <li>No external financing (lines of credit, overdrafts) unless explicitly selected.</li>
          <li>Vendor trust scores are entirely rule-based on mock data — not real registry lookups.</li>
          <li>Bill scan uses Gemini Vision; falls back to a hardcoded sample if the API is unavailable.</li>
        </ul>

        <h3 className="text-xl font-bold text-white mt-8 mb-4">What we do NOT claim</h3>
        <ul className="list-disc pl-5 space-y-2 text-zinc-400">
          <li>These are estimates, not predictions.</li>
          <li>Vendor scores are illustrative — consult official registries before making decisions.</li>
          <li>The AI scenario parser uses regex fallback — it does not &quot;understand&quot; language.</li>
        </ul>

        <div className="p-4 mt-8 rounded-xl bg-primary/10 border border-primary/20 text-center text-sm font-medium text-primary">
          &ldquo;The tool suggests; the owner decides.&rdquo;
        </div>
      </div>
    </div>
  );
}
