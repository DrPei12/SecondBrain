'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Edit, Trash2, Archive, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  status: string;
  created_at: string;
}

export default function NoteDetail() {
  const params = useParams();
  const router = useRouter();
  const [note, setNote] = useState<Note | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      fetchNote();
    }
  }, [params.id]);

  const fetchNote = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/notes/${params.id}`);
      if (res.ok) {
        const data = await res.json();
        setNote(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (status: string) => {
    try {
      await fetch(`http://localhost:8000/api/notes/${params.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      fetchNote();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteNote = async () => {
    if (!confirm('确定删除这篇笔记吗？')) return;
    
    try {
      await fetch(`http://localhost:8000/api/notes/${params.id}`, {
        method: 'DELETE'
      });
      router.push('/');
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (!note) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">笔记不存在</p>
          <Link href="/" className="text-primary-600 hover:underline">
            返回首页
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/" className="p-2 hover:bg-gray-100 rounded-lg">
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </Link>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{note.title}</h1>
                <p className="text-sm text-gray-500">
                  {new Date(note.created_at).toLocaleDateString('zh-CN')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {note.status !== 'Reviewed' && (
                <button
                  onClick={() => updateStatus('Reviewed')}
                  className="flex items-center gap-2 px-3 py-1.5 text-green-600 hover:bg-green-50 rounded-lg"
                >
                  <Check className="w-4 h-4" />
                  标记为已回顾
                </button>
              )}
              {note.status !== 'Archived' && (
                <button
                  onClick={() => updateStatus('Archived')}
                  className="flex items-center gap-2 px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  <Archive className="w-4 h-4" />
                  归档
                </button>
              )}
              <button
                onClick={deleteNote}
                className="flex items-center gap-2 px-3 py-1.5 text-red-600 hover:bg-red-50 rounded-lg"
              >
                <Trash2 className="w-4 h-4" />
                删除
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <article className="bg-white rounded-xl border border-gray-200 p-8">
          {/* Tags */}
          {note.tags && note.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {note.tags.map(tag => (
                <span 
                  key={tag}
                  className="px-3 py-1 bg-primary-50 text-primary-700 text-sm rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Title */}
          <h1 className="text-3xl font-bold text-gray-900 mb-6">{note.title}</h1>

          {/* Content */}
          <div className="prose prose-lg max-w-none prose-headings:font-bold prose-a:text-primary-600 prose-pre:bg-gray-900 prose-pre:p-4 prose-pre:rounded-lg prose-code:text-primary-700 prose-code:bg-primary-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {note.content || ''}
            </ReactMarkdown>
          </div>

          {/* Status Badge */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              note.status === 'Inbox' ? 'bg-yellow-100 text-yellow-700' :
              note.status === 'Reviewed' ? 'bg-green-100 text-green-700' :
              'bg-gray-100 text-gray-600'
            }`}>
              {note.status === 'Inbox' ? '📥 收件箱' : 
               note.status === 'Reviewed' ? '✅ 已回顾' : '📦 已归档'}
            </span>
          </div>
        </article>
      </main>
    </div>
  );
}
