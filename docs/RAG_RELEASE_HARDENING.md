# SecondBrain RAG Release Hardening

This checklist turns the live Bailian/DashScope validation into a repeatable
release gate. It intentionally keeps provider secrets out of git, reports, and
shell command lines.

## 1. Security

- Rotate any provider key that was pasted into chat, issue trackers, terminal
  logs, or screenshots before publishing.
- Store local provider credentials in `.secrets/dashscope.key` and point
  `DASHSCOPE_API_KEY_FILE` at that path. Do not commit `.secrets/`.
- Store deployment provider credentials in the host secret manager or process
  environment. Prefer `DASHSCOPE_API_KEY_FILE` / `BAILIAN_API_KEY_FILE` when the
  platform supports mounted secret files.
- Keep `SECOND_BRAIN_API_KEY` separate from provider credentials. Rotate it
  independently when sharing a staging backend.
- Run the tracked-file scanner before release:

```powershell
python scripts/check-rag-secrets.py
```

Expected result:

- No likely provider secrets found in tracked files.

## 2. Acceptance Gates

Run the local preflight first:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\rag-release-check.ps1 -Mode preflight
```

This verifies:

- local SecondBrain API key is configured
- Bailian/DashScope provider key is configured
- `LLM_PROVIDER=bailian`
- `BAILIAN_LLM_MODEL=qwen3.6-plus`
- `BAILIAN_ENABLE_THINKING=false`
- `BAILIAN_EMBEDDING_MODEL=text-embedding-v4`
- `BAILIAN_EMBEDDING_DIMENSIONS=1024`
- existing SecondBrain notes are present

Run the no-network fake-provider smoke when changing RAG plumbing:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\rag-release-check.ps1 -Mode fake
```

Fake-provider smoke validates the API, authentication, rebuild, non-mock response,
and grounded-source plumbing without spending real provider quota. It does not
grade retrieval ranking quality because the local fake embeddings are deterministic
test doubles.

Run the live release gate only when a real provider key is available:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\rag-release-check.ps1 -Mode live
```

Live acceptance requires:

- `/api/health/ready` returns `status=ready`
- provider is `bailian`
- model is `qwen3.6-plus`
- thinking is disabled
- rebuild indexes existing notes with `failed_count=0`
- RAG answers are non-empty
- `mock=false`
- grounded sources are returned
- source hints are found
- modality metadata is preserved for files ingested through `/api/rag/ingest`

## 3. Quality Evaluation

The release query set lives in `tests/rag_quality_questions.json`.

It covers:

- Agent learning plans
- technical tutorials
- product-management notes
- Scrum workflow notes
- agent architecture notes
- daily/session/operations notes
- long-term memory notes

The live check records:

- category
- source hint hit
- source titles
- answer length
- latency
- mock flag
- failure reasons

Reports are runtime artifacts and should remain ignored.

## 4. Product Experience

The Ask page should expose release-critical state without requiring a terminal:

- RAG ready/degraded status
- provider, engine, document count, chunk count, average latency
- rebuild index action
- query latency
- mock warning
- empty-source warning
- expandable grounded sources
- file ingestion for text, tables, documents, and media captions

## 4.1 Multimodal Ingestion Scope

SecondBrain follows the RAG-Anything pattern of parsing files into
modality-aware content units before indexing. The current implementation keeps
the storage model note-backed:

- text, Markdown, HTML, JSON, and code files are indexed as text
- CSV, TSV, and XLSX files are rendered as markdown tables
- PDF, DOCX, and PPTX files are parsed through Python document parsers
- images are indexed by metadata plus optional user captions
- audio and video are indexed by metadata plus optional transcripts
- LaTeX-style equations inside text are tagged as `modality:equation`

This is not yet full native visual/audio reasoning. Add OCR, ASR, and VLM
captioning before treating image, audio, or video retrieval as semantic content
coverage.

## 5. Operations

The backend RAG health payload includes:

- vector store file size and update time
- last index job status
- index retry count
- recent index/query events
- query count, failure count, last latency, average latency
- explicit note that provider cost data is not yet available from the wrapper

Release operators should keep provider billing dashboards enabled until token
usage is captured directly from the provider wrapper.

## 6. Local Change Hygiene

Current local non-release data is intentionally kept separate from release
hardening commits unless explicitly staged:

- `backend/database.json` contains a local note data addition.
- `memory/` contains generated memory material and displays mojibake in the
  Windows shell output.

The `backend/app/models/note.py` status-column change is release-relevant: it
keeps note workflow status compatible with existing string values in SQLite and
JSON data. Keep it with the release hardening changes after tests pass.

## Final Release Evidence

Before marking a RAG release candidate ready, collect:

- `python scripts/check-rag-secrets.py`
- `python tests/test_rag_performance.py --preflight`
- fake-provider smoke output, if RAG plumbing changed
- live report summary, if provider key is available
- frontend build result
- git commit and push SHA
