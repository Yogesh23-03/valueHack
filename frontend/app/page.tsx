import Link from 'next/link';

export default function Home() {
  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)] items-center justify-center text-center">
      <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
        See the chain <br />
        <span className="text-gradient">before it happens.</span>
      </h1>
      <p className="text-xl text-zinc-400 mb-10 max-w-2xl">
        A fire-drill cascade simulator for small businesses. Discover how one disruption propagates into a cash-flow gap.
      </p>
      <div className="flex items-center gap-4">
        <Link href="/fire-drill" className="px-8 py-4 rounded-xl bg-gradient-to-r from-primary to-blue-500 font-bold text-white shadow-[0_0_40px_rgba(124,92,255,0.35)] hover:scale-105 transition-transform">
          Open the Fire Drill
        </Link>
        <Link href="/dashboard" className="px-8 py-4 rounded-xl glass border border-white/10 font-medium hover:bg-white/5 transition-colors">
          View the dashboard
        </Link>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 w-full max-w-5xl">
        {['Load your business', 'Run a fire drill', 'Compare actions'].map((title, i) => (
          <div key={i} className="glass p-6 rounded-2xl border border-white/5">
            <h3 className="font-semibold text-lg mb-2">{title}</h3>
            <p className="text-zinc-400 text-sm">Experience realistic scenario modeling using our deterministic cascade engine.</p>
          </div>
        ))}
      </div>
    </div>
  );
}
