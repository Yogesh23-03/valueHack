"use client";
export default function Report() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Decision Report</h1>
        <button onClick={() => window.print()} className="px-6 py-2 rounded-xl bg-primary text-white font-medium hover:bg-primary/90 transition">
          Print PDF
        </button>
      </div>

      <div className="glass p-12 rounded-3xl space-y-12 print:shadow-none print:glass-none print:bg-white print:text-black" style={{ minHeight: '800px' }}>
        <div className="border-b border-white/10 pb-6 print:border-zinc-200">
          <h2 className="text-4xl font-black mb-2">BizSim Report</h2>
          <p className="text-zinc-400 print:text-zinc-500">Sharma Hardware and Electricals</p>
        </div>

        <div className="space-y-4">
          <h3 className="text-xl font-bold">Situation</h3>
          <p className="text-zinc-300 print:text-zinc-700">Supplier A is projected to be 14 days late with the restock of fans and wiring.</p>
        </div>

        <div className="space-y-4">
          <h3 className="text-xl font-bold">Cascade Impact</h3>
          <ul className="list-disc pl-5 space-y-2 text-zinc-300 print:text-zinc-700">
            <li>Stock runs out on Day 10.</li>
            <li>Customer Verma&apos;s order is delayed.</li>
            <li>Cash drops below zero on Day 23.</li>
            <li>Payment to Supplier C fails on Day 25.</li>
          </ul>
        </div>

        <div className="space-y-4">
          <h3 className="text-xl font-bold">Suggested Action</h3>
          <div className="p-6 bg-white/5 rounded-xl border border-primary/30 print:bg-zinc-100 print:border-zinc-300">
            <h4 className="font-bold text-lg mb-2">Combined Approach</h4>
            <p className="text-zinc-300 print:text-zinc-700">Ask Supplier C for a 15-day extension AND offer a 2% early payment discount to customers.</p>
            <p className="text-sm mt-4 text-green-400 font-medium print:text-green-700">
              Result: Protects cash runway, zero failed payables, minimum cash stays positive at ₹12,000.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-xl font-bold">Assumptions</h3>
          <ul className="list-disc pl-5 space-y-2 text-zinc-400 text-sm print:text-zinc-600">
            <li>Demand rates are held constant at historical averages.</li>
            <li>No external financing modeled (overdraft, credit line).</li>
            <li>All numbers are estimates based on synthetic demo data — not predictions.</li>
          </ul>
        </div>

        <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center text-sm text-zinc-400 print:bg-zinc-50 print:border-zinc-200">
          The tool suggests; the owner decides. BizSim uses synthetic data for demonstration.
        </div>
      </div>
    </div>
  );
}
