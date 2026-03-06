#!/usr/bin/env python3
"""
SecondBrain RAG Performance Test Suite

Tests RAG retrieval performance with Evan's memory files.
Measures latency, accuracy, and retrieval quality.
"""

import socket
# Force IPv4 to avoid WSL2 localhost resolution issues
_original_getaddrinfo = socket.getaddrinfo
def _getaddrinfo(*args, **kwargs):
    results = _original_getaddrinfo(*args, **kwargs)
    return [r for r in results if r[0] == socket.AF_INET] or results
socket.getaddrinfo = _getaddrinfo

import requests
import time
import json
from pathlib import Path
from datetime import datetime

# Configuration
API_BASE = "http://127.0.0.1:8000/api"  # Use IPv4 to avoid resolution issues
MEMORY_DIR = Path("/mnt/d/Desktop/SecondBrain/data/evan-memory")

# Test queries with expected results
TEST_QUERIES = [
    {
        "query": "ErrorPare Phase 2.1 完成了哪些功能",
        "expected_keywords": ["配置系统", "规则引擎", "LLM 分析器", "npm 发布"],
        "category": "project_status"
    },
    {
        "query": "GitHub Token 是什么",
        "expected_keywords": ["ghp_", "DrPei12", "errorpare"],
        "category": "credentials"
    },
    {
        "query": "OpenAI API Key 相关讨论",
        "expected_keywords": ["sk-proj", "Codex", "API Key"],
        "category": "credentials"
    },
    {
        "query": "Cherry Sub-agent 连接问题",
        "expected_keywords": ["Cherry", "连接失败", "allowlist", "OpenClaw"],
        "category": "technical_issue"
    },
    {
        "query": "SecondBrain 项目架构",
        "expected_keywords": ["Next.js", "FastAPI", "LightRAG", "RAG"],
        "category": "architecture"
    },
    {
        "query": "2026 年 2 月 25 日发生了什么",
        "expected_keywords": ["heartbeat", "连接错误", "Brave Search"],
        "category": "timeline"
    },
    {
        "query": "Evan 的能力配置",
        "expected_keywords": ["Web Search", "Brave API", "Codex Deep Search"],
        "category": "capabilities"
    },
    {
        "query": "CEO 的偏好设置",
        "expected_keywords": ["CTO-level", "Zero-trust", "BLUF"],
        "category": "preferences"
    }
]


class RAGTestSuite:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        
    def check_api_health(self):
        """Check if API is running"""
        try:
            # Try root endpoint first (always available)
            resp = requests.get("http://127.0.0.1:8000/", timeout=5)
            if resp.status_code == 200:
                return True
        except Exception as e:
            print(f"Health check error: {e}")
            pass
        
        # Fallback to /api/health
        try:
            resp = requests.get(f"{API_BASE}/health", timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def get_rag_stats(self):
        """Get current RAG statistics"""
        try:
            resp = requests.get(f"{API_BASE}/rag/stats", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"Failed to get stats: {e}")
        return {}
    
    def index_memory_files(self):
        """Index all memory files into RAG"""
        print("\n📥 Indexing memory files...")
        
        # Read all memory files
        memory_files = list(MEMORY_DIR.glob("*.md"))
        print(f"Found {len(memory_files)} memory files")
        
        indexed = 0
        failed = 0
        
        for file_path in memory_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                title = file_path.stem  # Use filename as title
                
                # Create note via API
                note_data = {
                    "title": title,
                    "content": content,
                    "tags": ["memory", "evan", file_path.stem[:7]],  # Date tag
                    "source_url": None,
                    "status": "Reviewed"
                }
                
                resp = requests.post(
                    f"{API_BASE}/notes/",
                    json=note_data,
                    timeout=30
                )
                
                if resp.status_code in [200, 201]:
                    indexed += 1
                    print(f"  ✅ {title}")
                else:
                    failed += 1
                    print(f"  ❌ {title}: {resp.status_code}")
                    
            except Exception as e:
                failed += 1
                print(f"  ❌ {file_path.name}: {str(e)[:50]}")
        
        print(f"\nIndexing complete: {indexed} success, {failed} failed")
        return indexed, failed
    
    def trigger_rag_indexing(self):
        """Trigger RAG indexing for all notes"""
        print("\n🔄 Triggering RAG indexing...")
        
        try:
            resp = requests.post(
                f"{API_BASE}/rag/index",
                json={"force_reindex": True},
                timeout=60
            )
            
            if resp.status_code == 200:
                result = resp.json()
                print(f"  Indexed: {result.get('indexed_count', 0)} notes")
                print(f"  Failed: {result.get('failed_count', 0)} notes")
                return result
            else:
                print(f"  Error: {resp.status_code}")
                return None
                
        except Exception as e:
            print(f"  Error: {e}")
            return None
    
    def test_query(self, test_case):
        """Test a single query"""
        query = test_case["query"]
        expected = test_case["expected_keywords"]
        category = test_case["category"]
        
        start = time.time()
        
        try:
            resp = requests.post(
                f"{API_BASE}/rag/query",
                json={
                    "query": query,
                    "mode": "mix",
                    "top_k": 5
                },
                timeout=30
            )
            
            latency = (time.time() - start) * 1000  # ms
            
            if resp.status_code == 200:
                result = resp.json()
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                
                # Check keyword recall
                found_keywords = [kw for kw in expected if kw.lower() in answer.lower()]
                recall = len(found_keywords) / len(expected) if expected else 0
                
                test_result = {
                    "query": query,
                    "category": category,
                    "latency_ms": round(latency, 2),
                    "answer_length": len(answer),
                    "sources_count": len(sources),
                    "expected_keywords": expected,
                    "found_keywords": found_keywords,
                    "recall": round(recall, 2),
                    "success": resp.status_code == 200
                }
                
                # Status emoji
                status = "✅" if recall > 0.5 else "⚠️" if recall > 0 else "❌"
                print(f"  {status} {category}: {latency:.0f}ms, recall: {recall:.0%}")
                
                return test_result
            else:
                print(f"  ❌ {category}: HTTP {resp.status_code}")
                return {
                    "query": query,
                    "category": category,
                    "error": f"HTTP {resp.status_code}",
                    "success": False
                }
                
        except Exception as e:
            print(f"  ❌ {category}: {str(e)[:50]}")
            return {
                "query": query,
                "category": category,
                "error": str(e),
                "success": False
            }
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 60)
        print("SecondBrain RAG Performance Test Suite")
        print("=" * 60)
        print(f"Start time: {self.start_time}")
        print(f"Memory files: {MEMORY_DIR}")
        print(f"API endpoint: {API_BASE}")
        print("=" * 60)
        
        # Check API health
        print("\n🏥 Checking API health...")
        if not self.check_api_health():
            print("❌ API is not responding. Please start the backend server.")
            return False
        print("✅ API is healthy")
        
        # Get initial stats
        print("\n📊 Initial RAG stats:")
        initial_stats = self.get_rag_stats()
        print(f"  Working dir: {initial_stats.get('working_dir', 'N/A')}")
        print(f"  Initialized: {initial_stats.get('initialized', False)}")
        
        # Index memory files
        indexed, failed = self.index_memory_files()
        if indexed == 0:
            print("⚠️ No files indexed, continuing with existing data...")
        
        # Trigger RAG indexing
        self.trigger_rag_indexing()
        
        # Run query tests
        print("\n🔍 Running query tests...")
        for test_case in TEST_QUERIES:
            result = self.test_query(test_case)
            self.results.append(result)
            time.sleep(0.5)  # Rate limiting
        
        # Generate report
        self.generate_report()
        
        return True
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("TEST REPORT")
        print("=" * 60)
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get("success", False))
        high_recall = sum(1 for r in self.results if r.get("recall", 0) > 0.5)
        
        latencies = [r.get("latency_ms", 0) for r in self.results if r.get("latency_ms")]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else (latencies[0] if latencies else 0)
        
        recalls = [r.get("recall", 0) for r in self.results if r.get("recall") is not None]
        avg_recall = sum(recalls) / len(recalls) if recalls else 0
        
        print(f"""
Summary:
  Total queries:     {total}
  Successful:        {successful} ({successful/total*100:.0f}%)
  High recall (>50%): {high_recall} ({high_recall/total*100:.0f}%)

Performance:
  Avg latency:       {avg_latency:.0f}ms
  P95 latency:       {p95_latency:.0f}ms
  Avg recall:        {avg_recall:.0%}

Detailed Results:
""")
        
        for i, result in enumerate(self.results, 1):
            status = "✅" if result.get("recall", 0) > 0.5 else "⚠️" if result.get("recall", 0) > 0 else "❌"
            print(f"  {i}. {status} [{result.get('category', 'N/A')}]")
            print(f"     Query: {result.get('query', 'N/A')[:60]}...")
            print(f"     Latency: {result.get('latency_ms', 'N/A')}ms, Recall: {result.get('recall', 'N/A')}")
            if result.get('found_keywords'):
                print(f"     Found: {', '.join(result['found_keywords'])}")
            print()
        
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_queries": total,
                "successful": successful,
                "high_recall": high_recall,
                "avg_latency_ms": round(avg_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "avg_recall": round(avg_recall, 2)
            },
            "results": self.results
        }
        
        report_path = Path("/mnt/d/Desktop/SecondBrain/tests/rag_test_report.json")
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        
        print(f"📄 Report saved to: {report_path}")
        print("=" * 60)


if __name__ == "__main__":
    suite = RAGTestSuite()
    suite.run_all_tests()
