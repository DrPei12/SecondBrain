'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Clock,
  Database,
  RefreshCw,
  Send,
  Server,
  Sparkles,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { apiFetch } from '@/lib/api';

interface Source {
  id: string;
  note_id?: string;
  chunk_id?: string;
  title: string;
  snippet?: string;
  relevance: number;
  source_url?: string | null;
}

interface Answer {
  query: string;
  answer: string;
  sources: Source[];
  engine?: string;
  provider?: string;
  elapsed_ms?: number;
  mock?: boolean;
}

interface RagHealth {
  status: string;
  ready?: boolean;
  engine?: string;
  provider?: {
    name?: string;
    configured?: boolean;
    llm_model?: string;
    embedding_model?: string;
    embedding_dimensions?: number;
    thinking_enabled?: boolean;
  };
  degraded_reason?: string | null;
  vector_store?: {
    chunk_count?: number;
    document_count?: number;
    file_size_bytes?: number;
    updated_at?: string | null;
  };
  notes?: {
    total?: number;
    by_rag_status?: Record<string, number>;
  };
  operations?: {
    last_index_job?: {
      status?: string;
      indexed_count?: number;
      failed_count?: number;
      retry_count?: number;
      duration_ms?: number;
      ended_at?: string;
    } | null;
  };
  metrics?: {
    query?: {
      count?: number;
      failure_count?: number;
      average_latency_ms?: number | null;
      last_latency_ms?: number | null;
    };
  };
}

interface RebuildResult {
  indexed_count: number;
  failed_count: number;
  retry_count?: number;
  status: string;
  message: string;
}

const formatMs = (value?: number | null) =>
  typeof value === 'number' ? `${Math.round(value)}ms` : 'n/a';

export default function AskAI() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [health, setHealth] = useState<RagHealth | null>(null);
  const [rebuild, setRebuild] = useState<RebuildResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [healthLoading, setHealthLoading] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);

  const loadHealth = async () => {
    setHealthLoading(true);
    try {
      const res = await apiFetch('/api/rag/health');
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setHealth({
          status: 'degraded',
          degraded_reason: data.detail || 'RAG health check failed.',
        });
        return;
      }
      setHealth(data);
    } catch (e) {
      setHealth({
        status: 'degraded',
        degraded_reason: e instanceof Error ? e.message : 'RAG health check failed.',
      });
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const handleAsk = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch('/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          mode: 'mix',
          top_k: 5,
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.detail || 'RAG query failed.');
        setAnswer(null);
        await loadHealth();
        return;
      }

      setAnswer({
        query: data.query,
        answer: data.answer,
        sources: data.sources || [],
        engine: data.engine,
        provider: data.provider,
        elapsed_ms: data.elapsed_ms,
        mock: data.mock,
      });
      await loadHealth();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'RAG query failed.');
      setAnswer(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRebuild = async () => {
    setRebuilding(true);
    setError(null);
    setRebuild(null);
    try {
      const res = await apiFetch('/api/rag/rebuild', {
        method: 'POST',
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.detail || 'RAG rebuild failed.');
        return;
      }
      setRebuild(data);
      await loadHealth();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'RAG rebuild failed.');
    } finally {
      setRebuilding(false);
    }
  };

  const ready = health?.status === 'ready' || health?.ready;
  const statusTone = ready
    ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
    : 'border-amber-200 bg-amber-50 text-amber-900';

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-10 border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-5xl px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <Link href="/" className="rounded-lg p-2 hover:bg-gray-100" aria-label="Back">
                <ArrowLeft className="h-5 w-5 text-gray-600" />
              </Link>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-900">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Ask SecondBrain</h1>
                  <p className="text-sm text-gray-500">Grounded answers from indexed notes</p>
                </div>
              </div>
            </div>
            <button
              onClick={loadHealth}
              disabled={healthLoading}
              className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-50"
              aria-label="Refresh RAG health"
              title="Refresh RAG health"
            >
              <RefreshCw className={`h-4 w-4 ${healthLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        <section className={`mb-6 rounded-lg border p-4 ${statusTone}`}>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              {ready ? (
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" />
              ) : (
                <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
              )}
              <div>
                <p className="font-semibold">{ready ? 'RAG ready' : 'RAG degraded'}</p>
                <p className="mt-1 text-sm">
                  {health?.degraded_reason ||
                    `${health?.provider?.name || 'provider'} / ${health?.provider?.llm_model || 'model'} / ${health?.engine || 'engine'}`}
                </p>
              </div>
            </div>
            <button
              onClick={handleRebuild}
              disabled={rebuilding}
              className="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Database className="h-4 w-4" />
              {rebuilding ? 'Rebuilding' : 'Rebuild index'}
            </button>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric icon={Server} label="Provider" value={health?.provider?.name || 'n/a'} />
            <Metric
              icon={Database}
              label="Documents"
              value={`${health?.vector_store?.document_count ?? 0}/${health?.notes?.total ?? 0}`}
            />
            <Metric icon={BookOpen} label="Chunks" value={String(health?.vector_store?.chunk_count ?? 0)} />
            <Metric
              icon={Activity}
              label="Avg Latency"
              value={formatMs(health?.metrics?.query?.average_latency_ms)}
            />
          </div>
        </section>

        {rebuild && (
          <section className="mb-6 rounded-lg border border-gray-200 bg-white p-4 text-sm text-gray-700">
            <div className="flex flex-wrap items-center gap-4">
              <span className="font-semibold text-gray-900">{rebuild.status}</span>
              <span>{rebuild.message}</span>
              <span>Retries: {rebuild.retry_count ?? 0}</span>
            </div>
          </section>
        )}

        <section className="mb-6 rounded-lg border border-gray-200 bg-white p-5">
          <textarea
            placeholder="Ask about your notes..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                handleAsk();
              }
            }}
            className="h-32 w-full resize-none text-gray-700 outline-none"
          />
          <div className="mt-4 flex items-center justify-end">
            <button
              onClick={handleAsk}
              disabled={loading || !query.trim() || !ready}
              className="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
              {loading ? 'Querying' : 'Ask'}
            </button>
          </div>
        </section>

        {error && (
          <section className="mb-6 flex gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
            <p className="text-sm">{error}</p>
          </section>
        )}

        {answer && (
          <section className="rounded-lg border border-gray-200 bg-white p-6">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-900">
                  <Sparkles className="h-4 w-4 text-white" />
                </div>
                <h2 className="font-semibold text-gray-900">Answer</h2>
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                <span>{answer.provider || 'provider n/a'}</span>
                <span>{answer.engine || 'engine n/a'}</span>
                <span className="inline-flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  {formatMs(answer.elapsed_ms)}
                </span>
              </div>
            </div>

            {answer.mock && (
              <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                This response is marked as mock and should not be used for production validation.
              </div>
            )}

            <div className="prose prose-gray max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer.answer}</ReactMarkdown>
            </div>

            <div className="mt-6 border-t border-gray-200 pt-4">
              <h3 className="mb-3 text-sm font-semibold text-gray-500">Sources</h3>
              {answer.sources.length === 0 ? (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                  No grounded sources were returned for this answer.
                </div>
              ) : (
                <div className="space-y-3">
                  {answer.sources.map((source) => (
                    <details
                      key={source.chunk_id || source.id}
                      className="rounded-lg border border-gray-200 bg-gray-50 p-3 open:bg-white"
                    >
                      <summary className="flex cursor-pointer list-none items-center gap-3">
                        <BookOpen className="h-4 w-4 text-gray-400" />
                        <Link
                          href={`/note/${source.note_id || source.id}`}
                          className="font-medium text-gray-800 hover:text-gray-950"
                        >
                          {source.title}
                        </Link>
                        <span className="ml-auto text-xs text-gray-500">
                          {Math.round(source.relevance * 100)}%
                        </span>
                      </summary>
                      {source.snippet && (
                        <p className="mt-3 text-sm leading-6 text-gray-600">{source.snippet}</p>
                      )}
                    </details>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Server;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-white/70 bg-white/70 px-3 py-2 text-gray-800">
      <Icon className="h-4 w-4 text-gray-500" />
      <div className="min-w-0">
        <p className="text-xs text-gray-500">{label}</p>
        <p className="truncate text-sm font-semibold">{value}</p>
      </div>
    </div>
  );
}
