'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Send, Sparkles, BookOpen } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Source {
  id: string;
  title: string;
  relevance: number;
}

interface Answer {
  query: string;
  answer: string;
  sources: Source[];
}

export default function AskAI() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          mode: 'mix',
          top_k: 5
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setAnswer({
          query: data.query,
          answer: data.answer,
          sources: data.sources || []
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 hover:bg-gray-100 rounded-lg">
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-purple-500 rounded-xl flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">智能问答</h1>
                <p className="text-sm text-gray-500">用自然语言查询你的知识库</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Search Box */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <textarea
            placeholder="输入你的问题，例如：\n- 关于 Next.js 开发，有什么最佳实践？\n- 我之前学 AI 的笔记在哪里？\n- 总结一下关于项目管理的内容"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full h-32 resize-none focus:outline-none text-gray-700 leading-relaxed"
          />
          <div className="flex justify-end mt-4">
            <button
              onClick={handleAsk}
              disabled={loading || !query.trim()}
              className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg hover:from-primary-700 hover:to-purple-700 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              {loading ? '思考中...' : '发送问题'}
            </button>
          </div>
        </div>

        {/* Answer */}
        {answer && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 bg-gradient-to-r from-primary-500 to-purple-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <h2 className="font-semibold text-gray-900">AI 回答</h2>
            </div>
            
            <div className="prose prose-lg max-w-none mb-6 prose-headings:font-bold prose-a:text-primary-600 prose-pre:bg-gray-900 prose-pre:p-4 prose-pre:rounded-lg">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {answer.answer}
              </ReactMarkdown>
            </div>

            {/* Sources */}
            {answer.sources.length > 0 && (
              <div className="pt-4 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-500 mb-3">参考来源</h3>
                <div className="space-y-2">
                  {answer.sources.map((source: Source) => (
                    <Link
                      key={source.id}
                      href={`/note/${source.id}`}
                      className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                    >
                      <BookOpen className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-700">{source.title}</span>
                      <span className="text-xs text-gray-400 ml-auto">
                        相关度 {Math.round(source.relevance * 100)}%
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tips */}
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-800 mb-2">💡 提问技巧</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• 使用具体的问题而非模糊的描述</li>
            <li>• 可以问"关于 X，我之前记录了什么"</li>
            <li>• 可以要求"总结关于 X 的内容"</li>
            <li>• 可以问"X 和 Y 有什么关联"</li>
          </ul>
        </div>
      </main>
    </div>
  );
}
