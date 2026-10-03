import os

def write_file(path, content):
    if os.path.dirname(path): os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

dashboard_page = """
"use client";
import { useEffect, useState } from 'react';
import { getBusiness, getAttention } from '@/lib/api';
import { AlertCircle, TrendingDown, Clock, Box, PieChart } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function Dashboard() {
  const [business, setBusiness] = useState<any>(null);
  const [attention, setAttention] = useState<any[]>([]);

  useEffect(() => {
    getBusiness().then(setBusiness).catch(console.error);
    getAttention().then(setAttention).catch(console.error);
  }, []);

  const data = [
    { name: 'Supplier A', value: 75 },
    { name: 'Supplier B', value: 15 },
    { name: 'Supplier C', value: 10 },
  ];

  if (!business) return <div className="p-8 text-center text-zinc-400">Loading dashboard...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: "Cash on hand", value: `₹${business.cash.toLocaleString()}` },
          { label: "Days of cover", value: "12 days" },
          { label: "At-risk payables", value: "₹70,000" },
          { label: "Supplier concentration", value: "75%" },
        ].map((metric, i) => (
          <div key={i} className="glass p-6 rounded-2xl">
            <p className="text-zinc-400 text-sm font-medium">{metric.label}</p>
            <p className="text-3xl font-bold font-mono mt-2">{metric.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass p-6 rounded-2xl">
          <h2 className="text-lg font-semibold mb-4">Today's Attention List</h2>
          <div className="space-y-3">
            {attention.map(item => (
              <div key={item.id} className="flex items-center gap-4 p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                <AlertCircle className="w-5 h-5 text-warning" />
                <span className="flex-1">{item.text}</span>
                <button className="text-xs text-primary font-medium px-3 py-1 rounded-full bg-primary/10 hover:bg-primary/20">Why?</button>
              </div>
            ))}
          </div>
        </div>
        
        <div className="glass p-6 rounded-2xl">
          <h2 className="text-lg font-semibold mb-4">Supplier Concentration</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} layout="vertical" margin={{ top: 0, right: 0, left: 20, bottom: 0 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{fill: '#A1A1AA', fontSize: 12}} />
                <Tooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{backgroundColor: '#12121A', borderColor: 'rgba(255,255,255,0.1)'}} />
                <Bar dataKey="value" fill="#7C5CFF" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
"""

fire_drill_page = """
"use client";
import { useState, useEffect } from 'react';
import { simulateCascade, compareActions } from '@/lib/api';
import { LineChart, Line, ReferenceLine, ResponsiveContainer, YAxis, XAxis, Tooltip } from 'recharts';
import { AlertTriangle, Play, Info } from 'lucide-react';

export default function FireDrill() {
  const [delay, setDelay] = useState(14);
  const [simResult, setSimResult] = useState<any>(null);
  const [actionsResult, setActionsResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const runSim = async () => {
    setLoading(true);
    try {
      const res = await simulateCascade({ delay });
      setSimResult(res);
      const acts = await compareActions(delay);
      setActionsResult(acts);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    runSim();
  }, [delay]); // auto-run on delay change for demo

  const chartData = simResult?.cash_timeline.map((c: number, i: number) => ({
    day: i + 1,
    cash: c,
    actionCash: actionsResult?.combined?.cash_timeline[i] || c,
    baseline: 50000 - (i*3000)
  })) || [];

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col md:flex-row gap-6">
      {/* Left: Params */}
      <div className="w-full md:w-80 glass p-6 rounded-2xl flex flex-col gap-6 overflow-y-auto">
        <h2 className="text-xl font-bold">Scenario Setup</h2>
        <div>
          <label className="text-sm text-zinc-400 mb-2 block">Supplier Delay (Days)</label>
          <input 
            type="range" min="0" max="30" value={delay} 
            onChange={e => setDelay(Number(e.target.value))}
            className="w-full accent-primary"
          />
          <div className="text-right font-mono mt-1">{delay} days</div>
        </div>
        <button onClick={runSim} className="w-full py-3 rounded-xl bg-primary text-white font-bold flex items-center justify-center gap-2 hover:bg-primary/90 transition">
          <Play className="w-4 h-4" /> Run Simulation
        </button>
      </div>

      {/* Center & Right: Cascade & Charts */}
      <div className="flex-1 flex flex-col gap-6 overflow-hidden">
        
        {/* Cascade Map Mockup */}
        <div className="flex-1 glass rounded-2xl p-6 relative flex flex-col items-center justify-center border border-white/5">
           <h3 className="absolute top-6 left-6 font-semibold">Cascade Flow</h3>
           <div className="flex items-center gap-4 text-sm font-medium">
             <div className="p-4 rounded-xl bg-red-500/20 text-red-400 border border-red-500/30">Supplier A (Late)</div>
             <div className="w-8 h-0.5 bg-red-500/50"></div>
             <div className={`p-4 rounded-xl border ${simResult?.stockout ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-white/5 border-white/10'}`}>
                Stock {simResult?.stockout && `(Out Day ${simResult.stockout})`}
             </div>
             <div className="w-8 h-0.5 bg-white/20"></div>
             <div className={`p-4 rounded-xl border ${simResult?.first_negative_day ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-white/5 border-white/10'}`}>
                Cash {simResult?.first_negative_day && `(Neg Day ${simResult.first_negative_day})`}
             </div>
           </div>
        </div>

        {/* Cash Chart */}
        <div className="h-64 glass p-6 rounded-2xl relative">
          <h3 className="font-semibold mb-4 absolute top-6 left-6 z-10">Cash Runway</h3>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 20, right: 20, left: 20, bottom: 0 }}>
              <XAxis dataKey="day" stroke="#A1A1AA" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#A1A1AA" fontSize={12} tickLine={false} axisLine={false} tickFormatter={v => `₹${v/1000}k`} />
              <Tooltip contentStyle={{backgroundColor: '#12121A', borderColor: 'rgba(255,255,255,0.1)'}} />
              <ReferenceLine y={0} stroke="#EF4444" strokeDasharray="3 3" />
              {simResult?.first_negative_day && (
                <ReferenceLine x={simResult.first_negative_day} stroke="#EF4444" strokeDasharray="3 3" label={{ position: 'top', value: 'Danger Day', fill: '#EF4444', fontSize: 12 }} />
              )}
              <Line type="monotone" dataKey="cash" stroke="#EF4444" strokeWidth={2} dot={false} name="Disrupted" />
              <Line type="monotone" dataKey="actionCash" stroke="#22C55E" strokeWidth={2} dot={false} name="After Action" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        {/* Actions Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {actionsResult && Object.entries(actionsResult).map(([key, res]: [string, any]) => (
            <div key={key} className={`p-4 rounded-xl border ${key === 'combined' ? 'border-primary/50 bg-primary/10' : 'border-white/5 bg-white/5'}`}>
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-semibold capitalize text-sm">{key.replace('_', ' ')}</h4>
                {key === 'combined' && <span className="text-[10px] uppercase font-bold text-primary bg-primary/20 px-2 py-0.5 rounded-full">Suggested</span>}
              </div>
              <p className="text-xs text-zinc-400">Min Cash: ₹{res.min_cash.toLocaleString()}</p>
              <p className="text-xs text-zinc-400">Failed Payables: {res.failed.length}</p>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
"""

vendor_check_page = """
"use client";
import { useState } from 'react';
import { checkVendor } from '@/lib/api';
import { Search, ShieldAlert, CheckCircle, AlertTriangle } from 'lucide-react';

export default function VendorCheck() {
  const [query, setQuery] = useState('New Distributor');
  const [result, setResult] = useState<any>(null);
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

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">Vendor Trust Check</h1>
        <p className="text-zinc-400">Verify a vendor's history before adding them to a scenario.</p>
      </div>

      <div className="glass p-2 rounded-full flex items-center gap-2 max-w-xl mx-auto border border-white/10">
        <div className="pl-4 text-zinc-400"><Search className="w-5 h-5" /></div>
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Enter GSTIN, PAN, or Company Name"
          className="flex-1 bg-transparent border-none outline-none text-white px-2 py-3"
        />
        <button onClick={handleCheck} disabled={loading} className="px-6 py-2.5 rounded-full bg-primary text-white font-medium hover:bg-primary/90 transition">
          {loading ? 'Checking...' : 'Check'}
        </button>
      </div>

      {result && (
        <div className="glass p-8 rounded-3xl animate-in fade-in slide-in-from-bottom-4 duration-500 flex flex-col md:flex-row gap-8 items-center border border-white/10 mt-12">
          <div className="flex-shrink-0 relative flex items-center justify-center w-48 h-48 rounded-full border-8 border-white/5">
             <div className={`text-6xl font-black font-mono ${result.badge === 'red' ? 'text-danger' : 'text-success'}`}>
               {result.score}
             </div>
             <svg className="absolute inset-0 w-full h-full -rotate-90">
               <circle cx="50%" cy="50%" r="46%" fill="none" stroke={result.badge === 'red' ? '#EF4444' : '#22C55E'} strokeWidth="8" strokeDasharray="300" strokeDashoffset={300 - (300 * result.score / 100)} className="transition-all duration-1000 ease-out" />
             </svg>
          </div>
          
          <div className="flex-1 space-y-4 w-full">
            <h3 className="text-xl font-bold">{query}</h3>
            <div className="space-y-2">
              {result.reasons.map((reason: string, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/5">
                  {result.badge === 'red' ? <AlertTriangle className="w-5 h-5 text-danger shrink-0 mt-0.5" /> : <CheckCircle className="w-5 h-5 text-success shrink-0 mt-0.5" />}
                  <span className="text-sm text-zinc-300">{reason}</span>
                </div>
              ))}
            </div>
            {result.badge === 'red' && (
              <div className="mt-4 p-4 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm font-medium text-center">
                High Risk: Not recommended for Fire Drill scenarios.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
"""

bill_scan_page = """
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
"""

report_page = """
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
      
      <div className="glass p-12 rounded-3xl space-y-12 bg-white text-black print:shadow-none print:p-0 print:border-none" style={{minHeight: '800px'}}>
         <div className="border-b border-zinc-200 pb-6">
           <h2 className="text-4xl font-black mb-2">BizSim Report</h2>
           <p className="text-zinc-500">Sharma Hardware and Electricals</p>
         </div>
         
         <div className="space-y-4">
           <h3 className="text-xl font-bold">Situation</h3>
           <p>Supplier A is projected to be 14 days late with the restock of fans and wiring.</p>
         </div>
         
         <div className="space-y-4">
           <h3 className="text-xl font-bold">Cascade Impact</h3>
           <ul className="list-disc pl-5 space-y-2">
             <li>Stock runs out on Day 10.</li>
             <li>Customer Verma's order is delayed.</li>
             <li>Cash drops below zero on Day 23.</li>
             <li>Payment to Supplier C fails on Day 25.</li>
           </ul>
         </div>
         
         <div className="space-y-4">
           <h3 className="text-xl font-bold">Suggested Action</h3>
           <div className="p-6 bg-zinc-100 rounded-xl border border-zinc-300">
             <h4 className="font-bold text-lg mb-2">Combined Approach</h4>
             <p>Ask Supplier C for a 15-day extension AND offer a 2% early payment discount to customers.</p>
             <p className="text-sm mt-4 text-green-700 font-medium">Result: Protects cash runway, zero failed payables, minimum cash stays positive at ₹12,000.</p>
           </div>
         </div>
      </div>
    </div>
  );
}
"""

about_page = """
"use client";
export default function About() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold">Model Card & Assumptions</h1>
      <div className="glass p-8 rounded-3xl space-y-6 text-zinc-300 leading-relaxed">
        <p><strong>Disclaimer:</strong> BizSim is a deterministic simulation engine designed to illustrate cash flow risks. It uses <em>synthetic data</em> for demonstration purposes.</p>
        
        <h3 className="text-xl font-bold text-white mt-8 mb-4">How it works</h3>
        <p>The engine steps through days 1 to 30. Each day it computes inventory drawdowns, accounts receivable collections, and accounts payable obligations. If cash drops below zero, subsequent payables are marked as failed.</p>
        
        <h3 className="text-xl font-bold text-white mt-8 mb-4">Assumptions</h3>
        <ul className="list-disc pl-5 space-y-2">
          <li>Demand is perfectly forecastable for the next 30 days (constant rate).</li>
          <li>Customers will pay exactly X days after delivery.</li>
          <li>No external financing (lines of credit, overdrafts) is modeled unless explicitly chosen as an action.</li>
        </ul>
        
        <div className="p-4 mt-8 rounded-xl bg-white/5 border border-white/10 text-center text-sm">
          "The tool suggests; the owner decides."
        </div>
      </div>
    </div>
  );
}
"""


write_file("frontend/app/dashboard/page.tsx", dashboard_page)
write_file("frontend/app/fire-drill/page.tsx", fire_drill_page)
write_file("frontend/app/vendor-check/page.tsx", vendor_check_page)
write_file("frontend/app/bill-scan/page.tsx", bill_scan_page)
write_file("frontend/app/report/page.tsx", report_page)
write_file("frontend/app/about/page.tsx", about_page)

docs_readme = """
# BizSim

BizSim is a fire-drill cascade simulator for small businesses. It shows how one disruption (a late supplier, a late customer, a cost spike) propagates through a business into a stock-out, delayed orders, a customer payment delay, and a cash-flow gap.

## Architecture
- **Frontend**: Next.js 14 (App Router), Tailwind CSS, Recharts, Framer Motion
- **Backend**: FastAPI, SQLModel, SQLite

## Local Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Demo Scenario
- **Business**: Sharma Hardware and Electricals
- **Baseline Scenario**: Supplier A is 14 days late.
- **Expected Outputs**: Stock-out on day 10, cash below zero on day 23, Supplier C payment fails on day 25.

## Data
This app uses **synthetic mock data**. The vendor checks and bill scans simulate AI and API lookups for demonstration purposes.

## Philosophy
BizSim provides estimates, not predictions. The tool suggests; the owner decides.
"""

docs_deploy = """
# Deploy and Demo Guide

## Deployment

### 1. Backend (Render)
- Create a new Web Service on Render, connect to this repo.
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variables:
  - `GEMINI_API_KEY`: (Your Google Gemini API Key, optional for fallback)

### 2. Frontend (Vercel)
- Create a new Project on Vercel, connect to this repo.
- Framework Preset: Next.js
- Root Directory: `frontend`
- Environment Variables:
  - `NEXT_PUBLIC_API_URL`: (The URL of your Render backend)

## 3-Minute Demo Script
1. **0:00** — "Small businesses see suppliers, stock, orders, payments one at a time. But a late supplier becomes a stock-out, a late customer payment, and a cash gap. BizSim shows that chain before it happens."
2. **0:20** — Point at the landing hero animation.
3. **0:35** — Open Fire Drill. Set delay to 14. "Supplier A is 14 days late." Point at the cascade map lighting up. "Restock slips from day 8 to day 22. Fans run out on day 10. Verma order goes late. Cash goes negative on day 23. Supplier C payment fails on day 25."
4. **1:10** — Point at cash runway chart. "The red line is zero. Here's the danger day."
5. **1:25** — Point at action cards. Click "Check New Distributor". "Score 32. Red. Registered 4 months ago, two cheque-bounce cases, missing GST filings. The cheaper vendor is a trap." Point at SUGGESTED tag. "The combined action — extension plus early discount — protects the owner best."
6. **2:10** — Point at Why? panel. "Every number has a reason, every estimate has an assumption."
7. **2:30** — Open Report. "One-page decision report." Click Print.
8. **2:50** — "BizSim. See the chain before it happens."

## Judge Questions Checklist
- **Q: Is this real data?** A: We used realistic synthetic data to model the engine.
- **Q: How does the AI work?** A: Gemini is used for unstructured tasks like plain-language scenario parsing and bill scanning. The financial engine is purely deterministic and fully explainable.
"""

write_file("README.md", docs_readme)
write_file("docs/DEPLOY_AND_DEMO.md", docs_deploy)
write_file("docs/ASSUMPTIONS.md", "BizSim uses deterministic modeling, assuming constant run-rates and strict term enforcement for the scenario window.")

print("Remaining pages and docs generated successfully.")
