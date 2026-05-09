#!/bin/bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000/api}"
SECOND_BRAIN_API_KEY="${SECOND_BRAIN_API_KEY:-}"

if [ -z "$SECOND_BRAIN_API_KEY" ]; then
  echo "SECOND_BRAIN_API_KEY is required" >&2
  exit 1
fi

header_key=(-H "X-API-Key: $SECOND_BRAIN_API_KEY" -H "Content-Type: application/json")

echo "Checking API readiness..."
curl -fsS "${API_BASE}/health/ready" | python -m json.tool

echo "Rebuilding RAG index from existing notes..."
curl -fsS -X POST "${API_BASE}/rag/rebuild" "${header_key[@]}" | python -m json.tool

echo "Running product RAG query..."
response="$(curl -fsS -X POST "${API_BASE}/rag/query" "${header_key[@]}" \
  -d '{"query":"Agent 学习规划主要讲了哪些学习方向？","mode":"mix","top_k":5}')"

echo "$response" | python -m json.tool

RESPONSE="$response" python - <<'PY'
import json
import os
import sys

data = json.loads(os.environ["RESPONSE"])
answer = data.get("answer", "")
sources = data.get("sources", [])
if data.get("mock") or "[Mock]" in answer:
    raise SystemExit("RAG returned mock output")
if not answer:
    raise SystemExit("RAG answer is empty")
if not sources:
    raise SystemExit("RAG sources are empty")
PY

echo "RAG shell smoke passed."
