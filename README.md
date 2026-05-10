# Second Brain - Personal Knowledge Management Platform

A lightweight "Personal Second Brain" web application for the CEO, built with Next.js + FastAPI.

## Tech Stack

- **Frontend:** Next.js (App Router) + Tailwind CSS + Shadcn/ui
- **Backend:** Python FastAPI
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **RAG:** LightRAG (from RAG-Anything)

## Project Structure

```
SecondBrain/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/
│   │   │       ├── notes.py
│   │   │       ├── rag.py
│   │   │       └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── connection.py
│   │   │   └── session.py
│   │   ├── models/
│   │   │   ├── note.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── note.py
│   │   │   └── rag.py
│   │   ├── services/
│   │   │   ├── note_service.py
│   │   │   └── rag_service.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── inbox/
│   │   │   │   ├── archive/
│   │   │   │   └── search/
│   │   │   ├── api/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── notes/
│   │   │   └── rag/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── utils.ts
│   │   └── types/
│   │       └── index.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
└── README.md
```

## Features

### Core Features
- **Note Management:** Create, read, update, delete notes with Markdown support
- **Status Workflow:** Inbox → Reviewed → Archived
- **Tag System:** Organize notes with tags
- **Source Tracking:** Link notes to original sources

### AI-Powered Features
- **RAG Integration:** Powered by LightRAG from RAG-Anything
- **Natural Language Q&A:** Query your knowledge base in natural language
- **Smart Summaries:** AI-generated summaries for notes

### API Interface
RESTful API endpoints for external AI Agents:
- `POST /api/notes` - Create notes (single or batch)
- `GET /api/notes` - List notes with filters
- `GET /api/notes/{id}` - Get note details
- `PUT /api/notes/{id}` - Update note
- `DELETE /api/notes/{id}` - Delete note
- `POST /api/rag/query` - RAG Q&A query
- `POST /api/rag/index` - Index notes for RAG

## Getting Started

### Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your configuration

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

### Product RAG Setup

SecondBrain now uses a real OpenAI-compatible RAG path in production:
notes are chunked, embedded, stored in a local JSON vector index, retrieved by
cosine similarity, and answered by the configured chat model with source
citations. Mock answers are not returned by the FastAPI RAG service.

For Bailian / DashScope validation:

```bash
cd backend
cp .env.example .env

# Required private values. Do not commit .env.
SECOND_BRAIN_API_KEY=dev-api-key
LLM_PROVIDER=bailian
DASHSCOPE_API_KEY=your-dashscope-key
# Or keep the key in a local file excluded from git:
# DASHSCOPE_API_KEY_FILE=.secrets/dashscope.key
BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
BAILIAN_LLM_MODEL=qwen3.6-plus
BAILIAN_ENABLE_THINKING=false
BAILIAN_EMBEDDING_MODEL=text-embedding-v4
BAILIAN_EMBEDDING_DIMENSIONS=1024
```

Useful RAG commands:

```bash
cd backend
secondbrain-rag stats
secondbrain-rag index --force
secondbrain-rag query "What did I write about Agent learning?"
```

Smoke test against an already running backend:

```bash
SECOND_BRAIN_API_KEY=dev-api-key python tests/test_rag_performance.py
```

REST API:

- `POST /api/rag/query` returns `answer`, `sources`, `provider`, `engine`, `elapsed_ms`, and `mock=false`.
- `POST /api/rag/index` indexes pending notes or requested note IDs.
- `POST /api/rag/rebuild` rebuilds the full local vector index from notes.
- `POST /api/rag/document/{note_id}/reindex` reindexes one note.
- `DELETE /api/rag/document/{note_id}` removes one note from the RAG index.
- `GET /api/rag/health` and `GET /api/health/ready` expose real readiness.

The local vector store lives at `RAG_VECTOR_STORE_FILE` and is regenerated when
the configured embedding model or dimension changes.

Security note: keep provider keys in local environment variables, deployment
secrets, or `.env` files excluded from git. Rotate any key that has been shared
in chat, logs, screenshots, or issue trackers before release.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## License

MIT License
