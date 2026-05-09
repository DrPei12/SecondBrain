'use client';

import { useState } from 'react';
import Link from 'next/link';
import { AlertCircle, ArrowLeft, BookOpen, Send, Sparkles } from 'lucide-react';
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

export default function AskAI() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
    } catch (e) {
      setError(e instanceof Error ? e.message : 'RAG query failed.');
      setAnswer(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-10 border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-4xl px-4 py-4">
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
                <p className="text-sm text-gray-500">Query your indexed notes with grounded sources.</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-8">
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
          <div className="mt-4 flex items-center justify-between gap-3">
            <span className="text-xs text-gray-400">Use Ctrl/Command + Enter to send</span>
            <button
              onClick={handleAsk}
              disabled={loading || !query.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
              {loading ? 'Querying...' : 'Ask'}
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
            <div className="mb-4 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-900">
                  <Sparkles className="h-4 w-4 text-white" />
                </div>
                <h2 className="font-semibold text-gray-900">Answer</h2>
              </div>
              <div className="text-xs text-gray-500">
                {[answer.provider, answer.engine, answer.elapsed_ms ? `${Math.round(answer.elapsed_ms)}ms` : null]
                  .filter(Boolean)
                  .join(' / ')}
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

            {answer.sources.length > 0 && (
              <div className="mt-6 border-t border-gray-200 pt-4">
                <h3 className="mb-3 text-sm font-semibold text-gray-500">Sources</h3>
                <div className="space-y-3">
                  {answer.sources.map((source) => (
                    <Link
                      key={source.chunk_id || source.id}
                      href={`/note/${source.note_id || source.id}`}
                      className="block rounded-lg border border-gray-200 bg-gray-50 p-3 hover:bg-gray-100"
                    >
                      <div className="flex items-center gap-3">
                        <BookOpen className="h-4 w-4 text-gray-400" />
                        <span className="font-medium text-gray-800">{source.title}</span>
                        <span className="ml-auto text-xs text-gray-500">
                          {Math.round(source.relevance * 100)}%
                        </span>
                      </div>
                      {source.snippet && (
                        <p className="mt-2 line-clamp-3 text-sm leading-6 text-gray-600">{source.snippet}</p>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
