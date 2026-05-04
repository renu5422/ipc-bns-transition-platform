// Shared TypeScript types for the IPC-BNS app
export interface Section {
  id: string;
  ipcCode: string;
  bnsCode: string;
  title: string;
  description: string;
}

export interface User {
  id: string;
  username: string;
  role: 'admin' | 'user';
}

export interface SearchResult {
  sections: Section[];
  total: number;
}
