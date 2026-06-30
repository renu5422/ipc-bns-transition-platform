'use client';

import { SectionMapping } from '@/types/section';
import clsx from 'clsx';

interface SectionCardProps {
  mapping: SectionMapping;
  score?: number;
  onClick?: (mapping: SectionMapping) => void;
}

const CONFIDENCE_LABEL: Record<string, string> = {
  HIGH: 'High confidence',
  MEDIUM: 'Medium confidence',
  LOW: 'Low confidence',
};

const CONFIDENCE_COLOR: Record<string, string> = {
  HIGH: 'bg-emerald-100 text-emerald-800',
  MEDIUM: 'bg-amber-100 text-amber-800',
  LOW: 'bg-red-100 text-red-800',
};

function scoreToConfidence(score?: number): 'HIGH' | 'MEDIUM' | 'LOW' {
  if (!score) return 'LOW';
  if (score >= 10) return 'HIGH';
  if (score >= 3) return 'MEDIUM';
  return 'LOW';
}

export default function SectionCard({ mapping, score, onClick }: SectionCardProps) {
  const confidence = scoreToConfidence(score);

  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={() => onClick?.(mapping)}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.(mapping)}
      className={clsx(
        'bg-white border border-slate-200 rounded-xl p-5 shadow-sm',
        'transition-all duration-150',
        onClick && 'cursor-pointer hover:border-amber-400 hover:shadow-md'
      )}
    >
      {/* Header: IPC → BNS codes */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="px-2.5 py-1 bg-slate-800 text-white text-xs font-mono font-bold rounded-md">
            {mapping.ipc_code}
          </span>
          <span className="text-slate-400 text-sm">→</span>
          <span className="px-2.5 py-1 bg-amber-500 text-slate-900 text-xs font-mono font-bold rounded-md">
            {mapping.bns_code}
          </span>
        </div>
        {score !== undefined && (
          <span
            className={clsx(
              'px-2 py-0.5 rounded-full text-xs font-semibold flex-shrink-0',
              CONFIDENCE_COLOR[confidence]
            )}
          >
            {CONFIDENCE_LABEL[confidence]}
          </span>
        )}
      </div>

      {/* Titles */}
      <div className="mb-2">
        <h3 className="text-slate-800 font-semibold text-sm leading-tight">
          {mapping.ipc_title}
        </h3>
        <p className="text-slate-500 text-xs mt-0.5">→ {mapping.bns_title}</p>
      </div>

      {/* Chapter badge */}
      <div className="mb-3">
        <span className="inline-block bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded-full">
          {mapping.chapter}
        </span>
      </div>

      {/* AI Summary */}
      {mapping.ai_summary && (
        <p className="text-slate-600 text-xs leading-relaxed mb-3">
          {mapping.ai_summary}
        </p>
      )}

      {/* Keywords */}
      {mapping.keywords?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {mapping.keywords.map((kw) => (
            <span
              key={kw}
              className="bg-slate-100 text-slate-500 text-xs px-2 py-0.5 rounded-md"
            >
              {kw}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
