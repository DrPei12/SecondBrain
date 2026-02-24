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

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## License

MIT License
