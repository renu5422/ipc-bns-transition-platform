export interface SectionMapping {
  id: string;

  ipc_code: string;
  ipc_title: string;

  bns_code: string;
  bns_title: string;

  description: string;

  chapter: string;

  keywords: string[];

  ai_summary: string;

  validation_rules: string[];

  created_at: string;
  updated_at: string;
}