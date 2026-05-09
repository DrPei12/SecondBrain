#!/usr/bin/env python3
"""
SecondBrain product RAG smoke test.

This script validates the real API path:
- API key authentication
- full RAG rebuild from existing notes
- non-mock query responses
- non-empty grounded sources
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


DEFAULT_QUERIES = [
    {
        "query": "Agent 学习规划主要讲了哪些学习方向？",
        "source_hint": "Agent 学习规划",
    },
    {
        "query": "在树莓派部署 OpenClaw 的关键步骤是什么？",
        "source_hint": "OpenClaw",
    },
    {
        "query": "外企敏捷研发 Scrum 的核心流程是什么？",
        "source_hint": "Scrum",
    },
    {
        "query": "Swarm 多智能体架构的核心思想是什么？",
        "source_hint": "Swarm",
    },
    {
        "query": "AI 产品经理与传统产品经理的主要差异有哪些？",
        "source_hint": "AI 产品经理",
    },
]


class ProductRAGSmoke:
    def __init__(self, api_base: str, api_key: str, timeout: int) -> None:
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }
        self.results: list[dict[str, Any]] = []

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        return requests.request(
            method,
            f"{self.api_base}{path}",
            headers=self.headers if path.startswith("/rag") or path.startswith("/notes") else None,
            timeout=self.timeout,
            **kwargs,
        )

    def check_health(self) -> dict[str, Any]:
        root_base = self.api_base[:-4] if self.api_base.endswith("/api") else self.api_base
        response = requests.get(f"{root_base}/", timeout=self.timeout)
        response.raise_for_status()

        ready = requests.get(
            f"{self.api_base}/health/ready",
            timeout=self.timeout,
        )
        ready.raise_for_status()
        return ready.json()

    def rebuild_index(self) -> dict[str, Any]:
        response = self.request("POST", "/rag/rebuild")
        response.raise_for_status()
        return response.json()

    def query(self, query: str, source_hint: str) -> dict[str, Any]:
        started = time.perf_counter()
        response = self.request(
            "POST",
            "/rag/query",
            json={"query": query, "mode": "mix", "top_k": 5},
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        response.raise_for_status()
        data = response.json()

        answer = data.get("answer", "")
        sources = data.get("sources", [])
        source_titles = [source.get("title", "") for source in sources]
        hinted = any(source_hint.lower() in title.lower() for title in source_titles)

        result = {
            "query": query,
            "source_hint": source_hint,
            "elapsed_ms": elapsed_ms,
            "answer_chars": len(answer),
            "sources_count": len(sources),
            "source_titles": source_titles,
            "hinted_source_found": hinted,
            "mock": bool(data.get("mock")),
            "passed": bool(answer)
            and not data.get("mock")
            and "[Mock]" not in answer
            and len(sources) > 0
            and hinted,
        }
        self.results.append(result)
        return result

    def run(self, queries: list[dict[str, str]]) -> dict[str, Any]:
        health = self.check_health()
        rebuild = self.rebuild_index()

        for item in queries:
            self.query(item["query"], item["source_hint"])

        passed = sum(1 for item in self.results if item["passed"])
        hinted = sum(1 for item in self.results if item["hinted_source_found"])
        return {
            "timestamp": datetime.now().isoformat(),
            "health": health,
            "rebuild": rebuild,
            "summary": {
                "total_queries": len(self.results),
                "passed": passed,
                "hinted_source_found": hinted,
                "all_passed": passed == len(self.results),
            },
            "results": self.results,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default=os.getenv("API_BASE", "http://127.0.0.1:8000/api"))
    parser.add_argument("--api-key", default=os.getenv("SECOND_BRAIN_API_KEY", ""))
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--report")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("SECOND_BRAIN_API_KEY or --api-key is required")

    suite = ProductRAGSmoke(args.api_base, args.api_key, args.timeout)
    report = suite.run(DEFAULT_QUERIES)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.report:
        path = Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0 if report["summary"]["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
