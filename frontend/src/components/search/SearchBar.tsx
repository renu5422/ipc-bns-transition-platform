'use client';

import { useState, FormEvent } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading?: boolean;
  placeholder?: string;
}

export default function SearchBar({
  onSearch,
  loading = false,
  placeholder = 'Search by keyword, IPC code, or BNS code…',
}: SearchBarProps) {
  const [query, setQuery] = useState('');

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed) onSearch(trimmed);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          disabled={loading}
          className="
            flex-1 px-4 py-3 rounded-lg border border-slate-300
            text-slate-800 placeholder-slate-400
            focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent
            disabled:bg-slate-100 disabled:cursor-not-allowed
            text-sm shadow-sm
          "
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="
            px-6 py-3 bg-amber-500 hover:bg-amber-600 text-slate-900
            font-semibold rounded-lg text-sm shadow-sm
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors
          "
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </div>
    </form>
  );
}
