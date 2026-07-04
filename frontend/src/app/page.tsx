// TARGET PATH IN REPO: frontend/src/app/page.tsx
'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import Navbar from '@/components/navbar/Navbar';
import { getHealth, HealthResponse } from '@/services/api';

const FEATURES = [
  {
    href: '/search',
    title: 'Legal Search',
    desc: 'Search by keyword, IPC code, or BNS code with deterministic ranking and confidence scoring.',
    icon: '🔍',
  },
  {
    href: '/chat',
    title: 'AI Assistant',
    desc: 'Ask migration questions in plain language — answers are grounded in validated mappings and always cite sections.',
    icon: '💬',
  },
  {
    href: '/dashboard',
    title: 'Platform Dashboard',
    desc: 'Live system health, module status, and endpoint diagnostics for the whole pipeline.',
    icon: '📊',
  },
] as const;

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      {/* Hero */}
      <section className="bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-4 py-20 text-center">
          <p className="text-amber-400 text-sm font-semibold tracking-widest uppercase mb-4">
            NyayaSetu AI
          </p>
          <h1 className="text-3xl sm:text-5xl font-bold tracking-tight mb-5">
            IPC ↔ BNS transition,
            <br className="hidden sm:block" /> with engineering-grade validation
          </h1>
          <p className="text-slate-300 max-w-2xl mx-auto text-sm sm:text-base leading-relaxed mb-8">
            Translate legacy Indian Penal Code references to the Bharatiya
            Nyaya Sanhita — deterministic rules first, AI reasoning second,
            every answer cited, scored, and auditable.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              href="/search"
              className="px-6 py-3 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold rounded-lg text-sm transition-colors"
            >
              Start searching
            </Link>
            <Link
              href="/chat"
              className="px-6 py-3 border border-slate-600 hover:border-slate-400 text-slate-200 font-semibold rounded-lg text-sm transition-colors"
            >
              Ask the AI assistant
            </Link>
          </div>
          {health && (
            <p className="mt-8 text-xs text-slate-500">
              API v{health.version} · {health.mapping_count} validated mapping
              record{health.mapping_count === 1 ? '' : 's'} ·{' '}
              <span className="text-emerald-400">● online</span>
            </p>
          )}
        </div>
      </section>

      {/* Feature cards */}
      <section className="max-w-6xl mx-auto px-4 py-14">
        <div className="grid sm:grid-cols-3 gap-5">
          {FEATURES.map((f) => (
            <Link
              key={f.href}
              href={f.href}
              className="card p-6 hover:border-amber-400 hover:shadow-md transition-all group"
            >
              <div className="text-2xl mb-3">{f.icon}</div>
              <h2 className="font-semibold text-slate-800 mb-1.5 group-hover:text-amber-700 transition-colors">
                {f.title}
              </h2>
              <p className="text-slate-500 text-sm leading-relaxed">{f.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Pipeline strip */}
      <section className="max-w-6xl mx-auto px-4 pb-16">
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">
            How every answer is produced
          </h3>
          <ol className="flex flex-col sm:flex-row gap-3 text-xs text-slate-500">
            {['Extract references', 'Retrieve validated mappings', 'Detect contradictions', 'Compose cited answer'].map(
              (step, i) => (
                <li key={step} className="flex items-center gap-2 flex-1">
                  <span className="w-5 h-5 rounded-full bg-slate-800 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                    {i + 1}
                  </span>
                  {step}
                  {i < 3 && <span className="hidden sm:inline text-slate-300 ml-auto">→</span>}
                </li>
              )
            )}
          </ol>
        </div>
      </section>
    </div>
  );
}
