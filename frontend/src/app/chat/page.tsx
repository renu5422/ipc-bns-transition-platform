'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import clsx from 'clsx';
import Navbar from '@/components/navbar/Navbar';
import {
  askAgent,
  askChat,
  AgentResponse,
  ChatResponse,
  ChatSource,
  Confidence,
} from '@/services/api';

type Mode = 'chat' | 'agent';

interface Message {
  role: 'user' | 'assistant';
  text: string;
  sources?: ChatSource[];
  confidence?: Confidence;
  trace?: string[];
  references?: string[];
  error?: boolean;
}

const CONFIDENCE_STYLE: Record<Confidence, string> = {
  high: 'bg-emerald-100 text-emerald-800',
  medium: 'bg-amber-100 text-amber-800',
  low: 'bg-orange-100 text-orange-800',
  none: 'bg-slate-100 text-slate-500',
};

const EXAMPLES = [
  'What replaced IPC-302?',
  'Which BNS section covers sexual assault?',
  'Compare IPC 302 and IPC 375',
];

export default function ChatPage() {
  const [mode, setMode] = useState<Mode>('chat');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || loading) return;
    setMessages((m) => [...m, { role: 'user', text: q }]);
    setInput('');
    setLoading(true);
    try {
      if (mode === 'agent') {
        const r: AgentResponse = await askAgent(q);
        setMessages((m) => [
          ...m,
          {
            role: 'assistant',
            text: r.answer,
            sources: r.sources,
            confidence: r.confidence,
            trace: r.trace,
            references: r.references,
          },
        ]);
      } else {
        const r: ChatResponse = await askChat(q);
        setMessages((m) => [
          ...m,
          { role: 'assistant', text: r.answer, sources: r.sources, confidence: r.confidence },
        ]);
      }
    } catch (err: unknown) {
      const status =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { status?: number } }).response?.status
          : undefined;
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          text:
            status === 401
              ? 'Please sign in to use the AI assistant (Sign in, top right). Your session may have expired.'
              : 'Could not reach the API. Is the backend running on port 8000?',
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="max-w-3xl w-full mx-auto px-4 py-8 flex-1 flex flex-col">
        {/* Header + mode toggle */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h1 className="text-xl font-bold text-slate-800">AI Legal Assistant</h1>
            <p className="text-slate-500 text-xs mt-0.5">
              Grounded in validated IPC ↔ BNS mappings — every answer cites its sections.
            </p>
          </div>
          <div className="flex rounded-lg border border-slate-200 bg-white p-0.5 text-xs font-medium self-start">
            {(['chat', 'agent'] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={clsx(
                  'px-3 py-1.5 rounded-md transition-colors',
                  mode === m
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-500 hover:text-slate-800'
                )}
              >
                {m === 'chat' ? 'Chat' : 'Agent (audit trace)'}
              </button>
            ))}
          </div>
        </div>

        {/* Message list */}
        <div className="flex-1 space-y-4 overflow-y-auto scroll-thin pb-4">
          {messages.length === 0 && (
            <div className="card p-8 text-center">
              <p className="text-slate-500 text-sm mb-4">
                Ask a migration question — try one of these:
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    onClick={() => send(ex)}
                    className="px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs text-slate-600 hover:border-amber-400 hover:text-amber-700 transition-colors"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) =>
            msg.role === 'user' ? (
              <div key={i} className="flex justify-end">
                <div className="bg-slate-800 text-white text-sm rounded-2xl rounded-br-sm px-4 py-2.5 max-w-[85%]">
                  {msg.text}
                </div>
              </div>
            ) : (
              <div key={i} className="flex justify-start">
                <div
                  className={clsx(
                    'card rounded-2xl rounded-bl-sm px-4 py-3 max-w-[85%] text-sm',
                    msg.error && 'border-red-200 bg-red-50 text-red-700'
                  )}
                >
                  <p className="whitespace-pre-wrap leading-relaxed text-slate-700">
                    {msg.text}
                  </p>

                  {(msg.confidence || (msg.sources && msg.sources.length > 0)) && (
                    <div className="flex flex-wrap items-center gap-1.5 mt-3">
                      {msg.confidence && (
                        <span className={clsx('badge', CONFIDENCE_STYLE[msg.confidence])}>
                          {msg.confidence} confidence
                        </span>
                      )}
                      {msg.sources?.map((s) => (
                        <span
                          key={s.id}
                          className="badge bg-slate-100 text-slate-600 font-mono"
                          title={`relevance score ${s.score}`}
                        >
                          {s.ipc_code} → {s.bns_code}
                        </span>
                      ))}
                    </div>
                  )}

                  {msg.trace && msg.trace.length > 0 && (
                    <details className="mt-3">
                      <summary className="text-xs text-slate-400 cursor-pointer hover:text-slate-600 select-none">
                        Audit trace ({msg.trace.length} steps)
                      </summary>
                      <ol className="mt-2 space-y-1 border-l-2 border-slate-200 pl-3">
                        {msg.trace.map((t, j) => (
                          <li key={j} className="text-xs text-slate-500 font-mono">
                            {t}
                          </li>
                        ))}
                      </ol>
                    </details>
                  )}
                </div>
              </div>
            )
          )}

          {loading && (
            <div className="flex justify-start">
              <div className="card rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-slate-400 animate-pulse">
                {mode === 'agent'
                  ? 'Running extract → retrieve → validate → compose…'
                  : 'Thinking…'}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Composer */}
        <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              mode === 'agent'
                ? 'Ask with section codes, e.g. "compare IPC 302 and BNS-101"…'
                : 'Ask a legal migration question…'
            }
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-lg border border-slate-300 text-sm text-slate-800 placeholder-slate-400 shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent disabled:bg-slate-100"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-3 bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold rounded-lg text-sm shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </form>
        <p className="text-[11px] text-slate-400 mt-2 text-center">
          Answers are drawn only from validated mapping data and are not legal advice.
        </p>
      </main>
    </div>
  );
}
