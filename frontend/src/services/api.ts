import axios from 'axios';
import { SectionMapping } from '@/types/section';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// ── Auth token handling ──────────────────────────────────────────────────
// Demo-grade storage: the JWT lives in localStorage (readable by any XSS).
// Acceptable for this research platform; use httpOnly cookies in production.

const TOKEN_KEY = 'nyayasetu_token';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
    window.dispatchEvent(new Event('auth-changed'));
  } catch {
    /* storage unavailable — stay logged out */
  }
}

export function clearToken(): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.removeItem(TOKEN_KEY);
    window.dispatchEvent(new Event('auth-changed'));
  } catch {
    /* ignore */
  }
}

export function isLoggedIn(): boolean {
  return getToken() !== null;
}

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status;
    const url: string = error?.config?.url ?? '';
    // A 401 from /login just means wrong credentials — keep any stored token.
    if (status === 401 && !url.includes('/login')) clearToken();
    return Promise.reject(error);
  }
);

// ── Response types ───────────────────────────────────────────────────────

export interface SearchResult {
  id: string;
  score: number;
  record: SectionMapping;
}

export interface SearchResponse {
  query: string;
  count: number;
  results: SearchResult[];
}

export interface MappingResult {
  ipc_code: string;
  ipc_title: string;
  bns_code: string;
  bns_title: string;
  description: string;
  chapter: string;
  keywords: string[];
  ai_summary: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface MappingResponse {
  query_code: string;
  direction: string;
  count: number;
  mappings: MappingResult[];
}

export interface ImpactItem {
  section_id: string;
  ipc_code: string;
  bns_code: string;
  ipc_title: string;
  relationship: string;
  chapter: string;
}

export interface ImpactResponse {
  section_id: string;
  total_records: number;
  unique_chapters: string[];
  impacted_sections: ImpactItem[];
  validation_rules: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  mapping_count: number;
}

export interface ChatSource {
  id: string;
  ipc_code: string;
  bns_code: string;
  score: number;
}

export type Confidence = 'high' | 'medium' | 'low' | 'none';

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  confidence: Confidence;
  model: string;
}

export interface AgentResponse {
  answer: string;
  references: string[];
  sources: ChatSource[];
  contradictions: Array<Record<string, unknown>>;
  confidence: Confidence;
  trace: string[];
  model: string;
}

export interface SummaryResponse {
  code: string;
  ipc_code: string;
  bns_code: string;
  summary: string;
  model: string;
}

// ── API functions ────────────────────────────────────────────────────────

export async function searchSections(
  query: string,
  limit = 10
): Promise<SearchResponse> {
  const { data } = await apiClient.get<SearchResponse>('/search', {
    params: { q: query, limit },
  });
  return data;
}

export async function getMapping(
  code: string,
  direction: 'ipc_to_bns' | 'bns_to_ipc' = 'ipc_to_bns'
): Promise<MappingResponse> {
  const { data } = await apiClient.get<MappingResponse>('/mapping', {
    params: { code, direction },
  });
  return data;
}

export async function getImpact(sectionId: string): Promise<ImpactResponse> {
  const { data } = await apiClient.get<ImpactResponse>('/mapping/impact', {
    params: { section_id: sectionId },
  });
  return data;
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health');
  return data;
}

export async function getAdminDiagnostics() {
  const { data } = await apiClient.get('/admin/diagnostics');
  return data;
}

export async function askChat(question: string): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>('/chat', { question });
  return data;
}

export async function askAgent(question: string): Promise<AgentResponse> {
  const { data } = await apiClient.post<AgentResponse>('/agent', { question });
  return data;
}

export async function getSummary(code: string): Promise<SummaryResponse> {
  const { data } = await apiClient.post<SummaryResponse>('/chat/summary', { code });
  return data;
}


export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/login', { username, password });
  setToken(data.access_token);
  return data;
}

export function logout(): void {
  clearToken();
}
