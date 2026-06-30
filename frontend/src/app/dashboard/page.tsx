'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/navbar/Navbar';
import { getHealth, getAdminDiagnostics } from '@/services/api';

interface HealthData {
  status: string;
  version: string;
  mapping_count: number;
}

interface DiagnosticsData {
  status: string;
  mapping_count: number;
  checks: { mapping_data_loaded: boolean; schema_valid: boolean };
}

const MODULE_STATUS = [
  { name: 'Retrieval Engine', status: 'In Progress' },
  { name: 'Aggregation Service', status: 'In Progress' },
  { name: 'Mapping Engine', status: 'Done' },
  { name: 'Contradiction Detector', status: 'In Progress' },
  { name: 'Impact Analysis', status: 'Done' },
  { name: 'Validation Pipeline', status: 'Partial' },
  { name: 'Diagnostics Layer', status: 'Done' },
  { name: 'Chatbot Engine', status: 'Prototype' },
] as const;

const STATUS_STYLE: Record<string, string> = {
  Done: 'bg-emerald-100 text-emerald-800',
  'In Progress': 'bg-amber-100 text-amber-800',
  Partial: 'bg-red-100 text-red-800',
  Prototype: 'bg-indigo-100 text-indigo-800',
  Planned: 'bg-slate-100 text-slate-600',
};

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const [h, d] = await Promise.all([getHealth(), getAdminDiagnostics()]);
      setHealth(h);
      setDiagnostics(d);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch {
      setError('Could not connect to the backend. Make sure it is running on port 8000.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchData(); }, []);

  const doneCount = MODULE_STATUS.filter((m) => m.status === 'Done').length;

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-slate-800">Project Dashboard</h1>
            <p className="text-slate-500 text-sm mt-0.5">IPC-BNS Transition Platform — live status</p>
          </div>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-slate-800 text-white text-sm rounded-lg hover:bg-slate-700 transition-colors"
          >
            ⟳ Refresh
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Stat cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard
            label="API Status"
            value={loading ? '…' : health?.status ?? 'unknown'}
            sub={`v${health?.version ?? '—'}`}
            color={health?.status === 'ok' ? 'text-emerald-600' : 'text-red-500'}
          />
          <StatCard
            label="Mapping Records"
            value={loading ? '…' : String(health?.mapping_count ?? '—')}
            sub="in dataset"
          />
          <StatCard
            label="Schema Valid"
            value={loading ? '…' : (diagnostics?.checks.schema_valid ? '✓ Yes' : '✗ No')}
            sub="data integrity"
            color={diagnostics?.checks.schema_valid ? 'text-emerald-600' : 'text-red-500'}
          />
          <StatCard
            label="Modules Done"
            value={`${doneCount} / ${MODULE_STATUS.length}`}
            sub="backend services"
          />
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Module tracker */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
              <h2 className="text-sm font-semibold text-slate-700">⚙️ Backend Modules</h2>
            </div>
            <ul className="divide-y divide-slate-100">
              {MODULE_STATUS.map(({ name, status }) => (
                <li key={name} className="flex items-center justify-between px-5 py-3">
                  <span className="text-sm text-slate-700">{name}</span>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${STATUS_STYLE[status] ?? ''}`}>
                    {status}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* API routes */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
              <h2 className="text-sm font-semibold text-slate-700">🔌 API Endpoints</h2>
            </div>
            <ul className="divide-y divide-slate-100 text-sm">
              {[
                { method: 'GET', path: '/health', status: 'Live' },
                { method: 'GET', path: '/search', status: 'Live' },
                { method: 'GET', path: '/mapping', status: 'Live' },
                { method: 'GET', path: '/mapping/contradiction', status: 'Live' },
                { method: 'GET', path: '/mapping/impact', status: 'Live' },
                { method: 'GET', path: '/admin/diagnostics', status: 'Live' },
                { method: 'POST', path: '/login', status: 'Stub' },
                { method: 'POST', path: '/api/chat', status: 'Planned' },
              ].map(({ method, path, status }) => (
                <li key={path} className="flex items-center justify-between px-5 py-2.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-indigo-600 w-10">{method}</span>
                    <span className="text-xs font-mono text-slate-600">{path}</span>
                  </div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    status === 'Live' ? 'bg-emerald-100 text-emerald-800'
                    : status === 'Stub' ? 'bg-amber-100 text-amber-800'
                    : 'bg-slate-100 text-slate-500'
                  }`}>
                    {status}
                  </span>
                </li>
              ))}
            </ul>
            {lastUpdated && (
              <p className="px-5 py-2 text-xs text-slate-400 border-t border-slate-100">
                Last updated: {lastUpdated}
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function StatCard({
  label, value, sub, color = 'text-slate-800',
}: { label: string; value: string; sub: string; color?: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-slate-400 mt-0.5">{sub}</p>
    </div>
  );
}
