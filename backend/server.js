/**
 * Second Brain API Server (Node.js Quick Start)
 * 
 * A simple Express server that provides the same API as the FastAPI backend
 * for quick testing without Python dependencies.
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');

// JSON file database
const DB_FILE = path.join(__dirname, 'database.json');

// Initialize database
function loadDb() {
    try {
        if (fs.existsSync(DB_FILE)) {
            const data = fs.readFileSync(DB_FILE, 'utf8');
            return JSON.parse(data);
        }
    } catch (e) {
        console.error('Error loading database:', e);
    }
    return { notes: [] };
}

function saveDb(data) {
    try {
        fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
    } catch (e) {
        console.error('Error saving database:', e);
    }
}

const db = loadDb();

// Initialize with sample data
db.notes = [
    {
        id: '1',
        title: '欢迎使用 Second Brain',
        content: '# Welcome to Second Brain\n\n这是一个轻量级的个人知识管理平台。\n\n## 核心功能\n\n- 📝 笔记管理\n- 🏷️ 标签系统\n- 🔍 搜索过滤\n- 🤖 RAG 智能问答\n\n## 使用方法\n\n1. 创建笔记\n2. 添加标签\n3. 浏览和回顾\n4. 智能问答',
        summary: null,
        tags: ['欢迎', '使用指南'],
        source_url: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: 'Inbox',
        indexed_for_rag: 'pending'
    },
    {
        id: '2',
        title: 'AI Agent 知识收集流程',
        content: '# AI Agent 知识收集\n\n外部 AI Agent 会自动通过 API 推送收集到的知识到本平台。\n\n## 推送格式\n\n```json\n{\n  "title": "笔记标题",\n  "content": "Markdown 内容",\n  "tags": ["标签1", "标签2"],\n  "source_url": "https://example.com"\n}\n```\n\n## 批量推送\n\n支持一次推送多条笔记。',
        summary: null,
        tags: ['AI', '自动化', '工作流'],
        source_url: null,
        created_at: new Date(Date.now() - 3600000).toISOString(),
        updated_at: new Date(Date.now() - 3600000).toISOString(),
        status: 'Inbox',
        indexed_for_rag: 'pending'
    }
];

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Request logging
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
    next();
});

// ==================== Health Endpoints ====================

app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy' });
});

app.get('/api/health/ready', (req, res) => {
    res.json({ status: 'ready', database: 'connected', rag: 'initialized' });
});

// ==================== Notes Endpoints ====================

// List notes with filters
app.get('/api/notes', (req, res) => {
    const { status, tags, search, page = 1, page_size = 20 } = req.query;
    
    let filtered = [...db.notes];
    
    // Apply filters
    if (status) {
        filtered = filtered.filter(n => n.status === status);
    }
    
    if (tags) {
        const tagList = tags.split(',');
        filtered = filtered.filter(n => 
            tagList.some(tag => n.tags.includes(tag))
        );
    }
    
    if (search) {
        const searchLower = search.toLowerCase();
        filtered = filtered.filter(n => 
            n.title.toLowerCase().includes(searchLower) ||
            (n.content && n.content.toLowerCase().includes(searchLower))
        );
    }
    
    // Sort by created_at desc
    filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    // Pagination
    const pageNum = parseInt(page);
    const size = parseInt(page_size);
    const start = (pageNum - 1) * size;
    const paginated = filtered.slice(start, start + size);
    
    res.json({
        items: paginated,
        total: filtered.length,
        page: pageNum,
        page_size: size
    });
});

// Get single note
app.get('/api/notes/:id', (req, res) => {
    const note = db.notes.find(n => n.id === req.params.id);
    if (!note) {
        return res.status(404).json({ detail: 'Note not found' });
    }
    res.json(note);
});

// Create single note
app.post('/api/notes', (req, res) => {
    const { title, content, tags, source_url, status } = req.body;
    
    const note = {
        id: uuidv4(),
        title,
        content: content || '',
        summary: null,
        tags: tags || [],
        source_url: source_url || null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: status || 'Inbox',
        indexed_for_rag: 'pending'
    };
    
    db.notes.push(note);
    saveDb(db);
    
    console.log(`✅ Created note: ${note.title}`);
    res.status(201).json(note);
});

// Create batch notes
app.post('/api/notes/batch', (req, res) => {
    const { notes } = req.body;
    
    if (!Array.isArray(notes)) {
        return res.status(400).json({ detail: 'Notes must be an array' });
    }
    
    const created = [];
    const failed = [];
    
    notes.forEach((noteData, idx) => {
        try {
            const note = {
                id: uuidv4(),
                title: noteData.title,
                content: noteData.content || '',
                summary: null,
                tags: noteData.tags || [],
                source_url: noteData.source_url || null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                status: noteData.status || 'Inbox',
                indexed_for_rag: 'pending'
            };
            db.notes.push(note);
            created.push(note);
            console.log(`✅ Created note: ${note.title}`);
        } catch (e) {
            failed.push({ index: idx, error: e.message, data: noteData });
        }
    });
    
    saveDb(db);
    
    res.json({
        created,
        failed,
        total_created: created.length,
        total_failed: failed.length
    });
});

// Update note
app.put('/api/notes/:id', (req, res) => {
    const idx = db.notes.findIndex(n => n.id === req.params.id);
    if (idx === -1) {
        return res.status(404).json({ detail: 'Note not found' });
    }
    
    const { title, content, tags, source_url, status } = req.body;
    
    // Update fields
    if (title !== undefined) db.notes[idx].title = title;
    if (content !== undefined) db.notes[idx].content = content;
    if (tags !== undefined) db.notes[idx].tags = tags;
    if (source_url !== undefined) db.notes[idx].source_url = source_url;
    if (status !== undefined) db.notes[idx].status = status;
    
    db.notes[idx].updated_at = new Date().toISOString();
    db.notes[idx].indexed_for_rag = 'pending';
    
    saveDb(db);
    res.json(db.notes[idx]);
});

// Delete note
app.delete('/api/notes/:id', (req, res) => {
    const idx = db.notes.findIndex(n => n.id === req.params.id);
    if (idx === -1) {
        return res.status(404).json({ detail: 'Note not found' });
    }
    
    db.notes.splice(idx, 1);
    saveDb(db);
    res.json({ message: 'Note deleted successfully' });
});

// ==================== RAG Endpoints (Mock) ====================

app.post('/api/rag/query', (req, res) => {
    const { query, mode = 'mix', top_k = 5 } = req.body;
    
    // Mock RAG response - in production, this would use LightRAG
    const relevantNotes = db.notes
        .filter(n => n.content && (
            n.content.toLowerCase().includes(query.toLowerCase().split(' ')[0]) ||
            n.title.toLowerCase().includes(query.toLowerCase().split(' ')[0])
        ))
        .slice(0, top_k);
    
    const answer = relevantNotes.length > 0 
        ? `根据您的问题"${query}"，我在笔记中找到了以下相关内容：\n\n` +
          relevantNotes.map(n => `- ${n.title}`).join('\n')
        : `我还没有关于"${query}"的笔记。让我帮您创建一条新的笔记记录这个问题。`;
    
    res.json({
        query,
        answer,
        sources: relevantNotes.map(n => ({
            id: n.id,
            title: n.title,
            relevance: Math.random() * 0.3 + 0.7
        })),
        mode
    });
});

app.post('/api/rag/index', (req, res) => {
    const { note_ids, force_reindex = false } = req.body || {};
    
    let toIndex = [];
    
    if (note_ids && Array.isArray(note_ids)) {
        toIndex = db.notes.filter(n => note_ids.includes(n.id));
    } else {
        toIndex = db.notes.filter(n => n.indexed_for_rag === 'pending');
    }
    
    toIndex.forEach(n => {
        n.indexed_for_rag = 'indexed';
    });
    
    saveDb(db);
    
    res.json({
        indexed_count: toIndex.length,
        failed_count: 0,
        status: 'complete',
        message: `Indexed ${toIndex.length} notes for RAG`
    });
});

app.get('/api/rag/stats', (req, res) => {
    res.json({
        working_dir: './rag_data',
        initialized: true,
        total_documents: db.notes.filter(n => n.indexed_for_rag === 'indexed').length,
        pending_documents: db.notes.filter(n => n.indexed_for_rag === 'pending').length
    });
});

// ==================== Root ====================

app.get('/', (req, res) => {
    res.json({
        name: 'Second Brain API',
        version: '0.1.0',
        status: 'running',
        docs: '/api/docs',
        notes_count: db.notes.length
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`
🚀 Second Brain API Server Started!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 Server: http://localhost:${PORT}
📚 API Docs: http://localhost:${PORT}/api/docs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Sample Endpoints:
   GET  /api/notes              - List all notes
   GET  /api/notes/:id         - Get note by ID
   POST /api/notes             - Create note
   POST /api/notes/batch       - Batch create notes
   PUT  /api/notes/:id         - Update note
   DELETE /api/notes/:id       - Delete note
   
🤖 RAG Endpoints:
   POST /api/rag/query          - Query knowledge base
   POST /api/rag/index         - Index notes
   GET  /api/rag/stats         - Get RAG stats
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    `);
});
