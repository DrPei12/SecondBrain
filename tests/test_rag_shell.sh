#!/bin/bash
# SecondBrain RAG Performance Test - Shell Version
# Tests RAG retrieval with Evan's memory files

set -e

API_BASE="http://127.0.0.1:8000/api"
MEMORY_DIR="/mnt/d/Desktop/SecondBrain/data/evan-memory"
REPORT_FILE="/mnt/d/Desktop/SecondBrain/tests/rag_test_report_$(date +%Y%m%d_%H%M%S).json"

echo "============================================================"
echo "SecondBrain RAG Performance Test Suite (Shell)"
echo "============================================================"
echo "Start time: $(date)"
echo "Memory files: $MEMORY_DIR"
echo "API endpoint: $API_BASE"
echo "============================================================"

# Check API health
echo ""
echo "🏥 Checking API health..."
if curl -s --max-time 5 "http://127.0.0.1:8000/" | grep -q "running"; then
    echo "✅ API is healthy"
else
    echo "❌ API is not responding"
    exit 1
fi

# Get RAG stats
echo ""
echo "📊 Initial RAG stats:"
curl -s "$API_BASE/rag/stats" | python3 -m json.tool 2>/dev/null || echo "  (stats endpoint not available)"

# Count memory files
MEMORY_COUNT=$(ls -1 "$MEMORY_DIR"/*.md 2>/dev/null | wc -l)
echo ""
echo "📁 Found $MEMORY_COUNT memory files"

# Index memory files as notes
echo ""
echo "📥 Indexing memory files as notes..."
INDEXED=0
FAILED=0

for file in "$MEMORY_DIR"/*.md; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        title="${filename%.md}"
        content=$(cat "$file")
        
        # Create note via API
        response=$(curl -s -X POST "$API_BASE/notes/" \
            -H "Content-Type: application/json" \
            -d "{
                \"title\": \"$title\",
                \"content\": \"$(echo "$content" | head -c 50000 | sed 's/"/\\"/g' | tr '\n' ' ')\",
                \"tags\": [\"memory\", \"evan\"],
                \"status\": \"Reviewed\"
            }" \
            --max-time 30 \
            -w "\n%{http_code}")
        
        http_code=$(echo "$response" | tail -1)
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
            echo "  ✅ $title"
            ((INDEXED++)) || true
        else
            echo "  ❌ $title (HTTP $http_code)"
            ((FAILED++)) || true
        fi
    fi
done

echo ""
echo "Indexing complete: $INDEXED success, $FAILED failed"

# Trigger RAG indexing
echo ""
echo "🔄 Triggering RAG indexing..."
rag_response=$(curl -s -X POST "$API_BASE/rag/index" \
    -H "Content-Type: application/json" \
    -d '{"force_reindex": true}' \
    --max-time 60)

echo "$rag_response" | python3 -m json.tool 2>/dev/null || echo "$rag_response"

# Test queries
echo ""
echo "🔍 Running query tests..."
echo ""

# Define test queries
declare -a QUERIES=(
    "ErrorPare Phase 2.1 完成了哪些功能"
    "GitHub Token 是什么"
    "Cherry Sub-agent 连接问题"
    "SecondBrain 项目架构"
    "Evan 的能力配置"
    "CEO 的偏好设置"
)

declare -a CATEGORIES=(
    "project_status"
    "credentials"
    "technical_issue"
    "architecture"
    "capabilities"
    "preferences"
)

RESULTS=()
TOTAL_LATENCY=0
QUERY_COUNT=0

for i in "${!QUERIES[@]}"; do
    query="${QUERIES[$i]}"
    category="${CATEGORIES[$i]}"
    
    start_time=$(date +%s%3N)
    
    response=$(curl -s -X POST "$API_BASE/rag/query" \
        -H "Content-Type: application/json" \
        -d "{
            \"query\": \"$query\",
            \"mode\": \"mix\",
            \"top_k\": 5
        }" \
        --max-time 30)
    
    end_time=$(date +%s%3N)
    latency=$((end_time - start_time))
    TOTAL_LATENCY=$((TOTAL_LATENCY + latency))
    ((QUERY_COUNT++)) || true
    
    # Extract answer length
    answer_length=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('answer','')))" 2>/dev/null || echo "0")
    
    status="✅"
    if [ "$answer_length" -gt 100 ]; then
        status="✅"
    elif [ "$answer_length" -gt 0 ]; then
        status="⚠️"
    else
        status="❌"
    fi
    
    echo "  $status [$category]: ${latency}ms, answer: ${answer_length} chars"
    
    RESULTS+=("{\"query\":\"$query\",\"category\":\"$category\",\"latency_ms\":$latency,\"answer_length\":$answer_length}")
    
    sleep 0.5
done

# Calculate averages
if [ $QUERY_COUNT -gt 0 ]; then
    AVG_LATENCY=$((TOTAL_LATENCY / QUERY_COUNT))
else
    AVG_LATENCY=0
fi

# Generate report
echo ""
echo "============================================================"
echo "TEST REPORT"
echo "============================================================"
echo ""
echo "Summary:"
echo "  Total queries: $QUERY_COUNT"
echo "  Avg latency:   ${AVG_LATENCY}ms"
echo "  Indexed files: $INDEXED"
echo ""

# Save JSON report
cat > "$REPORT_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "summary": {
    "total_queries": $QUERY_COUNT,
    "avg_latency_ms": $AVG_LATENCY,
    "indexed_files": $INDEXED,
    "failed_files": $FAILED
  },
  "results": [
    $(IFS=,; echo "${RESULTS[*]}")
  ]
}
EOF

echo "📄 Report saved to: $REPORT_FILE"
echo "============================================================"
