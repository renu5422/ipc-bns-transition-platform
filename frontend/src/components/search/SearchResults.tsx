'use client';

import { SectionMapping } from '@/types/section';
import SectionCard from '@/components/cards/SectionCard';

interface SearchResult {
  id: string;
  score: number;
  record: SectionMapping;
}

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  loading: boolean;
  error?: string | null;
}

export default function SearchResults({ results, query, loading, error }: SearchResultsProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-3 mt-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border border-slate-200 rounded-xl p-5 animate-pulse">
            <div className="flex gap-3 mb-4">
              <div className="h-6 w-20 bg-slate-200 rounded-md" />
              <div className="h-6 w-20 bg-amber-100 rounded-md" />
            </div>
            <div className="h-4 w-2/3 bg-slate-200 rounded mb-2" />
            <div className="h-3 w-1/2 bg-slate-100 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
        ⚠️ {error}
      </div>
    );
  }

  if (query && results.length === 0) {
    return (
      <div className="mt-8 text-center text-slate-500 text-sm">
        <div className="text-3xl mb-3">🔍</div>
        <p>No results found for <strong>"{query}"</strong>.</p>
        <p className="mt-1 text-xs text-slate-400">
          Try a different keyword or section code (e.g. IPC-302, murder, theft).
        </p>
      </div>
    );
  }

  if (!query) return null;

  return (
    <div className="mt-6">
      <p className="text-xs text-slate-500 mb-3">
        {results.length} result{results.length !== 1 ? 's' : ''} for{' '}
        <strong>"{query}"</strong>
      </p>
      <div className="flex flex-col gap-3">
        {results.map((r) => (
          <SectionCard key={r.id} mapping={r.record} score={r.score} />
        ))}
      </div>
    </div>
  );
}
