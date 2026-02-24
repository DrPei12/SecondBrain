'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Search, Plus, BookOpen, Settings, Sparkles } from 'lucide-react';

// Backend API URL - configurable via environment
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  status: string;
  created_at: string;
}

export default function Home() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNotes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      console.log(`Fetching from: ${API_URL}/api/notes?page_size=50`);
      const res = await fetch(`${API_URL}/api/notes?page_size=50`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data = await res.json();
      setNotes(data.items || []);
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to fetch notes';
      console.error('Failed to fetch notes:', e);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  const filteredNotes = notes.filter(note =>
    note.title.toLowerCase().includes(search.toLowerCase()) ||
    note.content.toLowerCase().includes(search.toLowerCase()) ||
    note.tags.some(tag => tag.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Second Brain</h1>
                <p className="text-sm text-gray-500">个人知识管理</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                <Settings className="w-5 h-5" />
              </button>
              <Link 
                href="/new"
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                <Plus className="w-4 h-4" />
                新建笔记
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Search Bar */}
        <div className="relative mb-8">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="搜索笔记、标签..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <span className="text-2xl">⚠️</span>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-red-800 mb-2">无法连接到后端服务</h3>
                <p className="text-sm text-red-600 mb-4">{error}</p>
                <div className="flex gap-3">
                  <button 
                    onClick={fetchNotes}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                  >
                    重试连接
                  </button>
                  <a 
                    href="http://localhost:8000/docs"
                    target="_blank"
                    className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-100 text-sm"
                  >
                    检查后端状态
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Stats */}
        {!error && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-4 rounded-xl border border-gray-200">
            <div className="text-3xl font-bold text-gray-900">{notes.length}</div>
            <div className="text-sm text-gray-500">全部笔记</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-gray-200">
            <div className="text-3xl font-bold text-yellow-600">
              {notes.filter(n => n.status === 'Inbox').length}
            </div>
            <div className="text-sm text-gray-500">收件箱</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-gray-200">
            <div className="text-3xl font-bold text-green-600">
              {notes.filter(n => n.status === 'Reviewed').length}
            </div>
            <div className="text-sm text-gray-500">已回顾</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-gray-200">
            <div className="text-3xl font-bold text-gray-600">
              {notes.filter(n => n.status === 'Archived').length}
            </div>
            <div className="text-sm text-gray-500">已归档</div>
          </div>
        </div>
        )}

        {/* Notes Grid */}
        <h2 className="text-lg font-semibold text-gray-900 mb-4">最近笔记</h2>
        
        {loading ? (
          <div className="text-center py-12 text-gray-500">
            加载中...
          </div>
        ) : filteredNotes.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
            <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">暂无笔记</p>
            <Link 
              href="/new"
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              <Plus className="w-4 h-4" />
              创建第一篇笔记
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredNotes.map(note => (
              <Link 
                key={note.id}
                href={`/note/${note.id}`}
                className="bg-white p-6 rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all"
              >
                <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                  {note.title}
                </h3>
                <p className="text-sm text-gray-500 mb-4 line-clamp-3">
                  {note.content?.slice(0, 150)}...
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {note.tags?.slice(0, 3).map(tag => (
                      <span 
                        key={tag}
                        className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    note.status === 'Inbox' ? 'bg-yellow-100 text-yellow-700' :
                    note.status === 'Reviewed' ? 'bg-green-100 text-green-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {note.status === 'Inbox' ? '收件箱' : 
                     note.status === 'Reviewed' ? '已回顾' : '已归档'}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* RAG Q&A Section */}
        <div className="mt-12 bg-gradient-to-r from-primary-50 to-purple-50 rounded-xl p-6 border border-primary-100">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-purple-500 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">智能问答</h3>
              <p className="text-sm text-gray-500">用自然语言查询你的知识库</p>
            </div>
          </div>
          <Link 
            href="/ask"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            开始问答
          </Link>
        </div>
      </main>
    </div>
  );
}
