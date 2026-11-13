'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/navbar/Navbar';
import { getAdminDiagnostics, getHealth, HealthResponse } from '@/services/api';
import clsx from 'clsx';

interface Diagnostics {
  status?: string;
  mapping_count?: number;
  checks?: Record<string, boolean>;
  [key: string]: unknown;
}

export default function AdminPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [diag, setDiag] = useState<Diagnostics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.allSettled([getHealth(), getAdminDiagnostics()]).then(([h, d]) => {
      if (h.status === 'fulfilled') setHealth(h.value);
      if (d.status === 'fulfilled') setDiag(d.value as Diagnostics);
      if (h.status === 'rejected' && d.status === 'rejected') {
        setError('Cannot reach the backend. Is it running on port 8000?');
      } else if (d.status === 'rejected') {
        const st = (d.reason as { response?: { status?: number } })?.response?.status;
        if (st === 401) setError('Admin diagnostics require sign-in — use the Sign in button in the navbar.');
      }
    });
  }, []);

  const checks = diag?.checks ?? {};

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800 mb-1">Admin · Diagnostics</h1>
          <p className="text-slate-500 text-sm">
            Live system checks from <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">/health</code>{' '}
            and <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">/admin/diagnostics</code>.
          </p>
        </div>

        {error && (
          <div className="card border-red-200 bg-red-50 p-4 text-sm text-red-700 mb-6">{error}</div>
        )}

        <div className="grid sm:grid-cols-3 gap-4 mb-8">
          <StatCard
            label="API status"
            value={health ? health.status.toUpperCase() : '—'}
            accent={health?.status === 'ok'}
          />
          <StatCard label="Version" value={health ? `v${health.version}` : '—'} />
          <StatCard
            label="Mapping records"
            value={health ? String(health.mapping_count) : '—'}
          />
        </div>

        <div className="card p-6">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">System checks</h2>
          {Object.keys(checks).length === 0 ? (
            <p className="text-slate-400 text-sm">No diagnostic checks reported.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {Object.entries(checks).map(([name, ok]) => (
                <li key={name} className="flex items-center justify-between py-2.5">
                  <span className="text-sm text-slate-600 font-mono">{name}</span>
                  <span
                    className={clsx(
                      'badge',
                      ok ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                    )}
                  >
                    {ok ? 'PASS' : 'FAIL'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="card p-5">
      <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{label}</p>
      <p className={clsx('text-2xl font-bold', accent ? 'text-emerald-600' : 'text-slate-800')}>
        {value}
      </p>
    </div>
  );
}
