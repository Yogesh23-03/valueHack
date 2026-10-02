"use client";
import { useEffect, useState } from 'react';
import { getBusiness, getAttention } from '@/lib/api';
import { AlertCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface AttentionItem {
  id: number;
  text: string;
  icon: string;
}

interface Business {
  name: string;
  cash: number;
}

export default function Dashboard() {
  const [business, setBusiness] = useState<Business | null>(null);
  const [attention, setAttention] = useState<AttentionItem[]>([]);

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
          { label: 'Cash on hand', value: `₹${business.cash.toLocaleString()}` },
          { label: 'Days of cover', value: '12 days' },
          { label: 'At-risk payables', value: '₹70,000' },
          { label: 'Supplier concentration', value: '75%' },
        ].map((metric, i) => (
          <div key={i} className="glass p-6 rounded-2xl">
            <p className="text-zinc-400 text-sm font-medium">{metric.label}</p>
            <p className="text-3xl font-bold font-mono mt-2">{metric.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass p-6 rounded-2xl">
          <h2 className="text-lg font-semibold mb-4">Today&apos;s Attention List</h2>
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
                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: '#A1A1AA', fontSize: 12 }} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: '#12121A', borderColor: 'rgba(255,255,255,0.1)' }} />
                <Bar dataKey="value" fill="#7C5CFF" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
