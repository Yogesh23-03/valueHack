"use client";
export default function BillScan() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 text-center">
      <h1 className="text-3xl font-bold">Bill Scan</h1>
      <p className="text-zinc-400">Upload a supplier invoice. AI will extract items, check taxes, and find price anomalies.</p>
      
      <div className="glass border-2 border-dashed border-white/20 p-24 rounded-3xl hover:border-primary/50 transition-colors cursor-pointer group">
        <div className="flex flex-col items-center justify-center text-zinc-400 group-hover:text-primary transition-colors">
          <svg className="w-12 h-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <span className="font-medium text-lg">Drag & drop an invoice (PDF/Image)</span>
          <span className="text-sm mt-2">or click to browse</span>
        </div>
      </div>
      
      <div className="flex justify-center gap-4 mt-8">
        <button className="px-6 py-3 rounded-xl glass text-sm hover:bg-white/5 transition">Use Sample Bill 1</button>
        <button className="px-6 py-3 rounded-xl glass text-sm hover:bg-white/5 transition">Use Sample Bill 2</button>
      </div>
    </div>
  );
}
