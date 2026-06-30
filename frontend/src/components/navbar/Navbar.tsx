'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';

const NAV_LINKS = [
  { href: '/search', label: 'Search' },
  { href: '/dashboard', label: 'Dashboard' },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="bg-slate-900 text-white shadow-md">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="text-amber-400 font-bold text-lg tracking-tight">
            ⚖️ IPC-BNS
          </span>
          <span className="hidden sm:inline text-slate-300 text-sm font-medium">
            Transition Platform
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={clsx(
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                pathname === href
                  ? 'bg-amber-500 text-slate-900'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              )}
            >
              {label}
            </Link>
          ))}
          <Link
            href="/admin"
            className="ml-2 px-3 py-1.5 rounded-md text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
          >
            Admin
          </Link>
        </div>
      </div>
    </nav>
  );
}
