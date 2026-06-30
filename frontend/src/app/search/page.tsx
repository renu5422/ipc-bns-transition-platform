'use client';

import { useState } from 'react';
import Navbar from '@/components/navbar/Navbar';
import SearchBar from '@/components/search/SearchBar';
import SearchResults from '@/components/search/SearchResults';
import { searchSections, SearchResult } from '@/services/api';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(q: string) {
    setQuery(q);
    setLoading(true);
    setError(null);
    try {
      const data = await searchSections(q);
      setResults(data.results);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Search failed. Is the backend running?';
      setError(msg);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <main className="max-w-3xl mx-auto px-4 py-10">
        {/* Page header */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-slate-800 mb-2">
            IPC ↔ BNS Legal Search
          </h1>
          <p className="text-slate-500 text-sm">
            Search by keyword, IPC section code, or BNS section code.
            Powered by deterministic ranking.
          </p>
        </div>

        {/* Search bar */}
        <SearchBar onSearch={handleSearch} loading={loading} />

        {/* Quick example chips */}
        {!query && (
          <div className="mt-4 flex flex-wrap gap-2 justify-center">
            {['IPC-302', 'murder', 'theft', 'IPC-375', 'sexual assault'].map((ex) => (
              <button
                key={ex}
                onClick={() => handleSearch(ex)}
                className="
                  px-3 py-1 bg-white border border-slate-200 rounded-full
                  text-xs text-slate-600 hover:border-amber-400 hover:text-amber-700
                  transition-colors shadow-sm
                "
              >
                {ex}
              </button>
            ))}
          </div>
        )}

        {/* Results */}
        <SearchResults
          results={results}
          query={query}
          loading={loading}
          error={error}
        />
      </main>
    </div>
  );
}
