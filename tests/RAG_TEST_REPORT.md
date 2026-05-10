# SecondBrain RAG Test Report

This file intentionally no longer stores the old Phase 1 mock-RAG benchmark.
That report was generated from the legacy mock path and is not valid evidence
for product readiness.

Current product validation is performed by:

- `tests/test_rag_performance.py`
- `tests/test_rag_shell.sh`

Required validation environment:

- FastAPI backend running
- `SECOND_BRAIN_API_KEY` configured in process env, `SECOND_BRAIN_ENV_FILE`,
  `backend/.env`, `.env`, `SECOND_BRAIN_API_KEY_FILE`, or passed as
  `--api-key`
- `LLM_PROVIDER=bailian`
- `DASHSCOPE_API_KEY` or `BAILIAN_API_KEY` configured outside git
- Or `DASHSCOPE_API_KEY_FILE` / `BAILIAN_API_KEY_FILE` pointing at a local
  secret file excluded from git
- `BAILIAN_LLM_MODEL=qwen3.6-plus`
- `BAILIAN_ENABLE_THINKING=false`
- `BAILIAN_EMBEDDING_MODEL=text-embedding-v4`

The live Bailian/DashScope report should be generated with:

```bash
python tests/test_rag_performance.py --report tests/RAG_LIVE_REPORT.json
```

Do not commit provider secrets or raw logs containing provider keys.
