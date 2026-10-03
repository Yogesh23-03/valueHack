import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

frontend_globals_css = """
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: #0A0A0F;
    --surface: rgba(18, 18, 26, 0.6);
    --surface-border: rgba(255, 255, 255, 0.06);
    --primary: #7C5CFF;
    --success: #22C55E;
    --warning: #F59E0B;
    --danger: #EF4444;
    --text-primary: #F5F5F7;
    --text-secondary: #A1A1AA;
    --text-muted: #71717A;
  }
}

body {
  color: var(--text-primary);
  background-color: var(--background);
  background-image: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(124,92,255,0.15), transparent),
                    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 100% 100%, 20px 20px, 20px 20px;
}

.glass {
  background: var(--surface);
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid var(--surface-border);
}

.glow {
  box-shadow: 0 0 40px rgba(124,92,255,0.35);
}

.text-gradient {
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-image: linear-gradient(135deg, #7C5CFF 0%, #4F9DFF 100%);
}
"""

frontend_tailwind_config = """
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0A0A0F",
        surface: "rgba(18, 18, 26, 0.6)",
        primary: "#7C5CFF",
        success: "#22C55E",
        warning: "#F59E0B",
        danger: "#EF4444",
      },
      animation: {
        shimmer: "shimmer 2s linear infinite",
        drift: "drift 10s ease-in-out infinite",
        "pulse-glow": "pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        shimmer: {
          from: { backgroundPosition: "200% 0" },
          to: { backgroundPosition: "-200% 0" },
        },
        drift: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-20px)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: ".5" },
        }
      }
    },
  },
  plugins: [],
};
export default config;
"""

frontend_layout = """
import "./globals.css";
import { Inter, JetBrains_Mono } from "next/font/google";
import TopNav from "@/components/nav/TopNav";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata = {
  title: "BizSim",
  description: "See the chain before it happens.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${mono.variable} font-sans antialiased min-h-screen relative`}>
        <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
          <div className="absolute top-20 left-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl animate-drift"></div>
          <div className="absolute top-40 right-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-drift delay-1000"></div>
          <div className="absolute bottom-20 left-1/2 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl animate-drift delay-2000"></div>
        </div>
        <TopNav />
        <main className="max-w-7xl mx-auto px-4 py-8 relative">
          {children}
        </main>
      </body>
    </html>
  );
}
"""

frontend_api = """
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchWithRetry(url: string, options: RequestInit = {}, retries = 1): Promise<any> {
  try {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const text = await res.text();
    return text ? JSON.parse(text) : {};
  } catch (error) {
    if (retries > 0) {
      await new Promise(r => setTimeout(r, 800));
      return fetchWithRetry(url, options, retries - 1);
    }
    throw error;
  }
}

export const getBusiness = () => fetchWithRetry(`${API}/api/business`);
export const getAttention = () => fetchWithRetry(`${API}/api/attention`);
export const simulateCascade = (params: any) => fetchWithRetry(`${API}/api/simulate/cascade`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(params),
});
export const compareActions = (delay: number) => fetchWithRetry(`${API}/api/actions/compare`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ delay }),
});
export const parseScenario = (text: string) => fetchWithRetry(`${API}/api/scenario/parse`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text }),
});
export const checkVendor = (input: any) => fetchWithRetry(`${API}/api/vendor/check`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(input),
});
export const scanBill = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return fetchWithRetry(`${API}/api/bill/scan`, {
    method: "POST",
    body: formData,
  });
};
export const getForecast = () => fetchWithRetry(`${API}/api/forecast`);
export const getAnomalies = () => fetchWithRetry(`${API}/api/anomalies`);

export const getReport = async () => {
  const res = await fetch(`${API}/api/report`);
  if (!res.ok) throw new Error("Failed to generate report");
  return await res.blob();
};
"""

frontend_topnav = """
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ShieldAlert, Github } from 'lucide-react';

export default function TopNav() {
  const pathname = usePathname();
  const links = [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/fire-drill', label: 'Fire Drill' },
    { href: '/vendor-check', label: 'Vendor Check' },
    { href: '/bill-scan', label: 'Bill Scan' },
    { href: '/report', label: 'Report' },
    { href: '/about', label: 'About' },
  ];

  return (
    <header className="sticky top-0 z-50 glass border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <ShieldAlert className="w-8 h-8 text-primary" />
          <span className="font-bold text-xl tracking-tight">BizSim</span>
        </Link>
        <nav className="hidden md:flex items-center gap-6">
          {links.map(link => (
            <Link 
              key={link.href} 
              href={link.href}
              className={`text-sm font-medium transition-colors ${
                pathname === link.href ? 'text-primary' : 'text-zinc-400 hover:text-zinc-100'
              }`}
            >
              {link.label}
              {pathname === link.href && (
                <div className="h-0.5 w-full bg-primary mt-1 absolute rounded-full" />
              )}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-4">
          <div className="px-3 py-1 rounded-full bg-zinc-800 text-xs font-medium text-zinc-300">
            Synthetic data
          </div>
          <a href="#" className="text-zinc-400 hover:text-white transition-colors">
            <Github className="w-5 h-5" />
          </a>
        </div>
      </div>
    </header>
  );
}
"""

frontend_page_tsx = """
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
"""


write_file("frontend/app/globals.css", frontend_globals_css)
write_file("frontend/tailwind.config.ts", frontend_tailwind_config)
write_file("frontend/app/layout.tsx", frontend_layout)
write_file("frontend/lib/api.ts", frontend_api)
write_file("frontend/components/nav/TopNav.tsx", frontend_topnav)
write_file("frontend/app/page.tsx", frontend_page_tsx)

print("Frontend files generated successfully.")
