# SecondBrain RAG Productization Audit

Audit date: 2026-05-10

## Objective

Upgrade SecondBrain from mock or half-finished RAG to a releasable product RAG
module with real indexing, real querying, source citations, readiness health,
Python package + REST API + SecondBrain integration, and live acceptance with
Bailian/DashScope `qwen3.6-plus` with thinking disabled against existing
SecondBrain documents.

## Evidence Checklist

| Requirement | Artifact / command | Status |
| --- | --- | --- |
| Real provider instead of mock-only responses | `backend/app/services/llm_provider.py` | Done |
| Bailian/DashScope OpenAI-compatible configuration | `backend/app/core/config.py`, `backend/.env.example` | Done |
| `qwen3.6-plus` configured as Bailian test model | `BAILIAN_LLM_MODEL=qwen3.6-plus` in config docs | Done |
| Thinking disabled for Bailian chat calls | `extra_body={"enable_thinking": false}` provider path | Done |
| Real embedding path | `text-embedding-v4`, `BAILIAN_EMBEDDING_DIMENSIONS=1024` | Done |
| Persistent local vector index | `backend/app/services/vector_store.py` | Done |
| Real query with source chunks | `backend/app/services/rag_service.py` returns `sources`, `mock=false` | Done |
| Real readiness health | `GET /api/health/ready`, `GET /api/rag/health` | Done |
| REST API rebuild/reindex/delete/query | `backend/app/api/endpoints/rag.py` | Done |
| Note lifecycle integration | `backend/app/api/endpoints/notes.py` indexes and deletes RAG docs best-effort | Done |
| Python package + CLI | `backend/pyproject.toml`, `secondbrain-rag` entry point | Done |
| Frontend asks real API and renders sources | `frontend/src/app/ask/page.tsx` | Done |
| Legacy Node quick-start cannot return mock RAG | `backend/server.js` returns unavailable/degraded for RAG | Done |
| Old mock report removed as acceptance evidence | `tests/RAG_TEST_REPORT.md` | Done |
| Product smoke test checks provider gates | `tests/test_rag_performance.py` validates ready, bailian, model, thinking, embedding, rebuild, non-mock sources; it can read `SECOND_BRAIN_API_KEY` from process env, `SECOND_BRAIN_ENV_FILE`, `backend/.env`, or `.env` | Done |
| Shell smoke checks non-mock + sources | `tests/test_rag_shell.sh` | Done |
| No committed provider secret | `.env`, secret files, live reports ignored | Done |
| Live Bailian query against existing SecondBrain docs | Requires local `DASHSCOPE_API_KEY`/`BAILIAN_API_KEY` or key-file plus `SECOND_BRAIN_API_KEY` | Blocked |

## Verification Performed

- `python -m py_compile` over changed backend RAG files and smoke scripts.
- `python -m py_compile tests/test_rag_performance.py` after adding local env-file fallback for the live smoke.
- `frontend` Next build passed after the Ask page update.
- `git diff --check` passed, with line-ending warnings only on local/user files.
- No-key FastAPI smoke: `LLM_PROVIDER=bailian`, model `qwen3.6-plus`,
  thinking disabled, readiness degraded, query returned HTTP 503.
- Fake OpenAI-compatible provider smoke: returned `mock=false` with sources.
- Node quick-start smoke: readiness degraded, RAG query HTTP 501,
  stats `ready=false`, `mock=false`.
- Secret-file loading smoke: fake UTF-8-BOM secret loaded via
  `DASHSCOPE_API_KEY_FILE`.

## Remaining Acceptance Gate

The goal is not complete until a real Bailian/DashScope credential is configured
outside git and the following acceptance command passes against existing
SecondBrain documents:

```bash
python tests/test_rag_performance.py --report tests/RAG_LIVE_REPORT.json
```

Expected acceptance evidence:

- `health.status == "ready"`
- provider name is `bailian`
- LLM model is `qwen3.6-plus`
- `thinking_enabled == false`
- embedding model is `text-embedding-v4`
- rebuild indexes existing notes with `failed_count == 0`
- every test query returns a non-empty answer
- every test query returns non-empty sources
- every test query has `mock == false`

Do not commit provider keys, local secret files, or live reports containing
sensitive note context.
