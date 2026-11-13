'use client';

import { useEffect, useState } from 'react';
import { isLoggedIn } from '@/services/api';

/** Reactive auth state — updates on login/logout in this or another tab. */
export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const sync = () => setIsAuthenticated(isLoggedIn());
    sync();
    window.addEventListener('auth-changed', sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener('auth-changed', sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  return { isAuthenticated };
}
