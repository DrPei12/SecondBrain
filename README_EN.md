# Second Brain - Personal Knowledge Management Platform

[English](README_EN.md) | [简体中文](README_CN.md)

Second Brain is a lightweight personal knowledge management web application built with Next.js and FastAPI. It helps a user capture notes, review and archive them, tag information, and query the personal knowledge base through a RAG-powered interface.

## Tech Stack

- **Frontend**: Next.js App Router, Tailwind CSS, Shadcn/ui-style components
- **Backend**: Python FastAPI
- **Database**: SQLite for development, PostgreSQL-ready architecture for production
- **RAG**: LightRAG from RAG-Anything
- **API style**: REST endpoints for notes and knowledge-base queries

## Project Structure

```text
SecondBrain/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/
│   │   │       ├── notes.py
│   │   │       ├── rag.py
│   │   │       └── health.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
└── README.md
```

## Features

### Core Knowledge Workflow

- Create, read, update, and delete Markdown notes.
- Move notes through an `Inbox -> Reviewed -> Archived` workflow.
- Organize notes with tags.
- Track original sources for captured knowledge.

### AI-Powered Features

- RAG integration powered by LightRAG.
- Natural-language Q&A over the personal knowledge base.
- AI-generated summaries for notes.

### API Interface

The backend exposes REST endpoints for external AI agents and frontend workflows:

- `POST /api/notes`: create one note or a batch of notes
- `GET /api/notes`: list notes with filters
- `GET /api/notes/{id}`: get note details
- `PUT /api/notes/{id}`: update a note
- `DELETE /api/notes/{id}`: delete a note
- `POST /api/rag/query`: ask a RAG question
- `POST /api/rag/index`: index notes for RAG

## Getting Started

### Backend Setup

```bash
cd backend
cp .env.example .env

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\venv\Scripts\Activate.ps1
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Root Convenience Scripts

```bash
npm run dev
npm run install:all
```

## Development Notes

- Keep notes and RAG indexing decoupled so note CRUD remains usable even if an embedding or LLM provider is unavailable.
- Keep source tracking explicit; the usefulness of a second brain depends on being able to trace knowledge back to origin.
- Treat the API as an integration surface for future agents, importers, and automation tools.

## License

MIT License.

