import axios from 'axios';
import { SectionMapping } from '@/types/section';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
});

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
