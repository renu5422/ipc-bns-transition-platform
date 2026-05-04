import { useState } from 'react';

export function useSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const search = async (q: string) => {
    setQuery(q);
    // TODO: call search API
  };

  return { query, results, search };
}
