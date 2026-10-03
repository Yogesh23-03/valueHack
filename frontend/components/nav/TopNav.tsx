"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ShieldAlert, Code } from 'lucide-react';

export default function TopNav() {
  const pathname = usePathname();
  const links = [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/fire-drill', label: 'Fire Drill' },
    { href: '/pricing', label: 'Price What-If' },
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
        <nav className="flex items-center gap-6 overflow-x-auto md:overflow-visible" aria-label="Main navigation">
          {links.map(link => (
            <Link 
              key={link.href} 
              href={link.href}
              className={`relative whitespace-nowrap text-sm font-medium transition-colors ${
                pathname === link.href ? 'text-primary' : 'text-zinc-400 hover:text-zinc-100'
              }`}
            >
              {link.label}
              {pathname === link.href && (
                <div className="absolute left-0 h-0.5 w-full rounded-full bg-primary" />
              )}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-4">
          <div className="px-3 py-1 rounded-full bg-zinc-800 text-xs font-medium text-zinc-300">
            Synthetic data
          </div>
          <a href="#" className="text-zinc-400 hover:text-white transition-colors">
            <Code className="w-5 h-5" />
          </a>
        </div>
      </div>
    </header>
  );
}
