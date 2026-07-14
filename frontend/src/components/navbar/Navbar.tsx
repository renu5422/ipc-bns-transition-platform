// TARGET PATH IN REPO: frontend/src/components/navbar/Navbar.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import { Scale, Search, MessageSquare, LayoutDashboard, Shield } from 'lucide-react';

const NAV_LINKS = [
  { href: '/search', label: 'Search', icon: Search },
  { href: '/chat', label: 'AI Assistant', icon: MessageSquare },
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    /* Glass: content scrolls beneath this bar, so the blur has real depth.
       This is the one place glassmorphism is unambiguously correct. */
    <nav className="glass-nav text-white sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <Scale
            className="w-5 h-5 text-amber-400 group-hover:rotate-6 transition-transform"
            aria-hidden="true"
          />
          <span className="text-amber-400 font-bold text-lg tracking-tight">
            NyayaSetu
          </span>
          <span className="hidden sm:inline text-slate-400 text-sm font-medium border-l border-white/10 pl-2 ml-1">
            IPC ↔ BNS Platform
          </span>
        </Link>

        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ href, label, icon: Icon }) => {
            const active = pathname?.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? 'page' : undefined}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  active
                    ? 'bg-amber-500 text-slate-900 shadow-sm shadow-amber-500/20'
                    : 'text-slate-300 hover:bg-white/10 hover:text-white'
                )}
              >
                <Icon className="w-4 h-4" aria-hidden="true" />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}

          <Link
            href="/admin"
            aria-current={pathname?.startsWith('/admin') ? 'page' : undefined}
            className={clsx(
              'ml-1.5 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
              pathname?.startsWith('/admin')
                ? 'bg-white/15 text-white'
                : 'text-slate-400 hover:text-white hover:bg-white/10'
            )}
          >
            <Shield className="w-3.5 h-3.5" aria-hidden="true" />
            <span className="hidden sm:inline">Admin</span>
          </Link>
        </div>
      </div>
    </nav>
  );
}
