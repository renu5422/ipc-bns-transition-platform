// TARGET PATH IN REPO: frontend/src/app/section/page.tsx  (replaces stub)
'use client';

import { FormEvent, Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Navbar from '@/components/navbar/Navbar';
import {
  getMapping,
  getSummary,
  MappingResult,
  SummaryResponse,
} from '@/services/api';
import clsx from 'clsx';

const CONFIDENCE_STYLE: Record<string, string> = {
  HIGH: 'bg-emerald-100 text-emerald-800',
  MEDIUM: 'bg-amber-100 text-amber-800',
  LOW: 'bg-red-100 text-red-800',
};

function SectionContent() {
  const params = useSearchParams();
  const initial = params?.get('code') ?? '';
  const [code, setCode] = useState(initial);
  const [query, setQuery] = useState(initial);
  const [mappings, setMappings] = useState<MappingResult[]>([]);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setSummary(null);
    Promise.allSettled([getMapping(query), getSummary(query)]).then(
      ([mapRes, sumRes]) => {
        if (cancelled) return;
        if (mapRes.status === 'fulfilled') {
          setMappings(mapRes.value.mappings);
        } else {
          setMappings([]);
          setError(`No validated mapping found for "${query}".`);
        }
        if (sumRes.status === 'fulfilled') setSummary(sumRes.value);
        setLoading(false);
      }
    );
    return () => {
      cancelled = true;
    };
  }, [query]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = code.trim();
    if (trimmed) setQuery(trimmed);
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-10">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Section Detail</h1>
        <p className="text-slate-500 text-sm">
          Look up one section by code for its full mapping, confidence, and AI summary.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-8">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Enter a section code, e.g. IPC-302 or BNS-101"
          className="flex-1 px-4 py-3 rounded-lg border border-slate-300 text-sm text-slate-800 placeholder-slate-400 shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent"
        />
        <button
          type="submit"
          disabled={loading || !code.trim()}
          className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold rounded-lg text-sm shadow-sm disabled:opacity-50 transition-colors"
        >
          {loading ? 'Loading…' : 'Look up'}
        </button>
      </form>

      {error && (
        <div className="card border-red-200 bg-red-50 p-4 text-sm text-red-700 mb-6">
          {error}
        </div>
      )}

      {mappings.map((m) => (
        <article key={`${m.ipc_code}-${m.bns_code}`} className="card p-6 mb-5">
          <div className="flex items-start justify-between gap-3 mb-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="code-chip bg-slate-800 text-white">{m.ipc_code}</span>
              <span className="text-slate-400">→</span>
              <span className="code-chip bg-amber-500 text-slate-900">{m.bns_code}</span>
            </div>
            <span className={clsx('badge', CONFIDENCE_STYLE[m.confidence])}>
              {m.confidence} confidence
            </span>
          </div>

          <h2 className="font-semibold text-slate-800">{m.ipc_title}</h2>
          <p className="text-slate-500 text-sm mb-4">→ {m.bns_title}</p>

          <dl className="grid sm:grid-cols-2 gap-4 text-sm mb-4">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400 mb-1">Chapter</dt>
              <dd className="text-slate-700">{m.chapter}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400 mb-1">Keywords</dt>
              <dd className="flex flex-wrap gap-1.5">
                {m.keywords.map((kw) => (
                  <span key={kw} className="badge bg-slate-100 text-slate-500">{kw}</span>
                ))}
              </dd>
            </div>
          </dl>

          <p className="text-slate-600 text-sm leading-relaxed">{m.description}</p>
        </article>
      ))}

      {summary && (
        <aside className="card border-amber-200 bg-amber-50/50 p-6">
          <h3 className="text-xs uppercase tracking-wide text-amber-700 font-semibold mb-2">
            AI-generated summary
          </h3>
          <p className="text-slate-700 text-sm leading-relaxed">{summary.summary}</p>
          <p className="text-[11px] text-slate-400 mt-3">
            Generated by {summary.model} · grounded in the validated record only.
          </p>
        </aside>
      )}
    </main>
  );
}

export default function SectionPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <Suspense>
        <SectionContent />
      </Suspense>
    </div>
  );
}
