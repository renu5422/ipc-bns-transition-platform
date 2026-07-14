// TARGET PATH IN REPO: frontend/src/app/page.tsx
'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import Navbar from '@/components/navbar/Navbar';
import { getHealth, HealthResponse } from '@/services/api';
import {
  Search,
  MessageSquare,
  LayoutDashboard,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

const FEATURES = [
  {
    href: '/search',
    title: 'Legal Search',
    desc: 'Search by keyword, IPC code, or BNS code with deterministic ranking and confidence scoring.',
    Icon: Search,
  },
  {
    href: '/chat',
    title: 'AI Assistant',
    desc: 'Ask migration questions in plain language — answers are grounded in validated mappings and always cite sections.',
    Icon: MessageSquare,
  },
  {
    href: '/dashboard',
    title: 'Platform Dashboard',
    desc: 'Live system health, module status, and endpoint diagnostics for the whole pipeline.',
    Icon: LayoutDashboard,
  },
] as const;

const PIPELINE = [
  'Extract references',
  'Retrieve validated mappings',
  'Detect contradictions',
  'Compose cited answer',
] as const;

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      {/* ── Hero ───────────────────────────────────────────────────────────
          The gradient mesh is what gives the glass below something to
          refract. Glass over a flat background is just a grey rectangle. */}
      <section className="relative hero-mesh hero-grain text-white overflow-hidden">
        <div className="relative max-w-6xl mx-auto px-4 pt-20 pb-32 text-center">
          <p className="text-amber-400 text-xs font-semibold tracking-[0.2em] uppercase mb-4">
            NyayaSetu AI
          </p>

          <h1 className="text-3xl sm:text-5xl font-bold tracking-tight mb-5">
            IPC ↔ BNS transition,
            <br className="hidden sm:block" />{' '}
            <span className="bg-gradient-to-r from-amber-300 to-amber-500 bg-clip-text text-transparent">
              with engineering-grade validation
            </span>
          </h1>

          <p className="text-slate-300 max-w-2xl mx-auto text-sm sm:text-base leading-relaxed mb-9">
            Translate legacy Indian Penal Code references to the Bharatiya Nyaya
            Sanhita — deterministic rules first, AI reasoning second, every
            answer cited, scored, and auditable.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/search"
              className="group flex items-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-400 text-slate-900 font-semibold rounded-xl text-sm transition-all hover:shadow-lg hover:shadow-amber-500/25"
            >
              Start searching
              <ArrowRight
                className="w-4 h-4 group-hover:translate-x-0.5 transition-transform"
                aria-hidden="true"
              />
            </Link>

            {/* Glass CTA — floats over the mesh, so the blur reads as depth. */}
            <Link
              href="/chat"
              className="glass-panel px-6 py-3 text-slate-100 font-semibold text-sm hover:bg-white/[0.16] transition-colors"
            >
              Ask the AI assistant
            </Link>
          </div>

          {/* Live status — translucent pill over the gradient. */}
          {health && (
            <div className="mt-9 flex justify-center">
              <span className="glass-pill text-slate-300">
                <ShieldCheck
                  className="w-3.5 h-3.5 text-emerald-400"
                  aria-hidden="true"
                />
                API v{health.version} · {health.mapping_count} validated mapping
                record{health.mapping_count === 1 ? '' : 's'}
                <span className="text-emerald-400">● online</span>
              </span>
            </div>
          )}
        </div>

        {/* Feature cards overlap the hero, so they sit ON the gradient —
            the one place card-level glass is justified. */}
        <div className="relative max-w-6xl mx-auto px-4 -mb-24">
          <div className="grid sm:grid-cols-3 gap-5">
            {FEATURES.map(({ href, title, desc, Icon }) => (
              <Link key={href} href={href} className="glass-card p-6 group">
                <Icon
                  className="w-6 h-6 text-amber-400 mb-3 group-hover:scale-110 transition-transform"
                  aria-hidden="true"
                />
                <h2 className="font-semibold text-white mb-1.5 group-hover:text-amber-300 transition-colors">
                  {title}
                </h2>
                <p className="text-slate-300/80 text-sm leading-relaxed">
                  {desc}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Spacer for the overlapping cards */}
      <div className="h-28" aria-hidden="true" />

      {/* ── Pipeline strip ─────────────────────────────────────────────────
          Solid card. This is explanatory content on a light background —
          glass here would only hurt legibility. */}
      <section className="max-w-6xl mx-auto px-4 pb-16">
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">
            How every answer is produced
          </h3>
          <ol className="flex flex-col sm:flex-row gap-3 text-xs text-slate-500">
            {PIPELINE.map((step, i) => (
              <li key={step} className="flex items-center gap-2 flex-1">
                <span className="w-5 h-5 rounded-full bg-slate-800 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
                  {i + 1}
                </span>
                {step}
                {i < PIPELINE.length - 1 && (
                  <ArrowRight
                    className="hidden sm:block w-3.5 h-3.5 text-slate-300 ml-auto shrink-0"
                    aria-hidden="true"
                  />
                )}
              </li>
            ))}
          </ol>
        </div>
      </section>
    </div>
  );
}
