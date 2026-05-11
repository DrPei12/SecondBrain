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
import sqlite3
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


def load_queries(path_value: str) -> list[dict[str, Any]]:
    if not path_value:
        return DEFAULT_QUERIES

    path = Path(path_value)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("queries", [])
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"No RAG quality queries found in {path}")

    queries: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"Query item #{index + 1} is not an object")
        query = str(item.get("query", "")).strip()
        source_hint = str(item.get("source_hint", "")).strip()
        if not query or not source_hint:
            raise ValueError(f"Query item #{index + 1} requires query and source_hint")
        queries.append(item)
    return queries


def _env_file_candidates() -> list[Path]:
    env_file = os.getenv("SECOND_BRAIN_ENV_FILE", "").strip()
    candidates = []
    if env_file:
        candidates.append(Path(env_file))
    candidates.extend([Path("backend/.env"), Path(".env")])
    return candidates


def _read_env_value(path: Path, key: str) -> str:
    """Read one simple KEY=VALUE entry without logging secrets."""
    if not path.is_file():
        return ""

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        return value.strip()
    return ""


def _read_secret_path(path_value: str, base_dir: Path = Path(".")) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.is_absolute():
        path = base_dir / path
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8-sig").strip()


def resolve_api_key(explicit: str) -> str:
    if explicit:
        return explicit

    env_value = os.getenv("SECOND_BRAIN_API_KEY", "").strip()
    if env_value:
        return env_value

    env_file_value = _read_secret_path(os.getenv("SECOND_BRAIN_API_KEY_FILE", "").strip())
    if env_file_value:
        return env_file_value

    for candidate in _env_file_candidates():
        value = _read_env_value(candidate, "SECOND_BRAIN_API_KEY")
        if value:
            return value
        file_value = _read_env_value(candidate, "SECOND_BRAIN_API_KEY_FILE")
        value = _read_secret_path(file_value, candidate.parent)
        if value:
            return value
    return ""


def _has_secret(value_keys: tuple[str, ...], file_keys: tuple[str, ...]) -> bool:
    for key in value_keys:
        if os.getenv(key, "").strip():
            return True
    for key in file_keys:
        if _read_secret_path(os.getenv(key, "").strip()):
            return True

    for candidate in _env_file_candidates():
        for key in value_keys:
            if _read_env_value(candidate, key):
                return True
        for key in file_keys:
            file_value = _read_env_value(candidate, key)
            if _read_secret_path(file_value, candidate.parent):
                return True
    return False


def _config_value(key: str, default: str = "") -> str:
    value = os.getenv(key, "").strip()
    if value:
        return value

    for candidate in _env_file_candidates():
        value = _read_env_value(candidate, key)
        if value:
            return value
    return default


def _local_note_counts() -> dict[str, Any]:
    db_path = Path("backend/second_brain.db")
    if not db_path.is_file():
        return {"database": str(db_path), "exists": False}

    with sqlite3.connect(db_path) as conn:
        notes = conn.execute("select count(*) from notes").fetchone()[0]
        non_empty = conn.execute(
            "select count(*) from notes "
            "where content is not null and length(trim(content)) != 0"
        ).fetchone()[0]
    return {
        "database": str(db_path),
        "exists": True,
        "notes_count": notes,
        "non_empty_notes": non_empty,
    }


def _bailian_config_status() -> dict[str, Any]:
    provider = _config_value("LLM_PROVIDER", "openai").strip().lower()
    llm_model = _config_value("BAILIAN_LLM_MODEL", "qwen3.6-plus").strip()
    embedding_model = _config_value(
        "BAILIAN_EMBEDDING_MODEL",
        "text-embedding-v4",
    ).strip()
    dimensions_raw = _config_value("BAILIAN_EMBEDDING_DIMENSIONS", "1024").strip()
    try:
        embedding_dimensions = int(dimensions_raw)
    except ValueError:
        embedding_dimensions = None
    thinking_enabled = (
        _config_value("BAILIAN_ENABLE_THINKING", "false").strip().lower() == "true"
    )

    return {
        "provider": provider,
        "llm_model": llm_model,
        "embedding_model": embedding_model,
        "embedding_dimensions": embedding_dimensions,
        "thinking_enabled": thinking_enabled,
        "provider_is_bailian": provider == "bailian",
        "llm_model_is_qwen36_plus": llm_model == "qwen3.6-plus",
        "embedding_model_is_text_embedding_v4": embedding_model == "text-embedding-v4",
        "embedding_dimensions_is_1024": embedding_dimensions == 1024,
        "thinking_disabled": thinking_enabled is False,
    }


def build_preflight_report(explicit_api_key: str = "") -> dict[str, Any]:
    api_key_configured = bool(resolve_api_key(explicit_api_key))
    provider_key_configured = _has_secret(
        ("DASHSCOPE_API_KEY", "BAILIAN_API_KEY"),
        ("DASHSCOPE_API_KEY_FILE", "BAILIAN_API_KEY_FILE"),
    )
    notes = _local_note_counts()
    notes_ready = bool(notes.get("non_empty_notes", 0) > 0)
    bailian_config = _bailian_config_status()
    config_ready = all(
        (
            bailian_config["provider_is_bailian"],
            bailian_config["llm_model_is_qwen36_plus"],
            bailian_config["embedding_model_is_text_embedding_v4"],
            bailian_config["embedding_dimensions_is_1024"],
            bailian_config["thinking_disabled"],
        )
    )
    return {
        "api_key_configured": api_key_configured,
        "bailian_provider_key_configured": provider_key_configured,
        "bailian_config": bailian_config,
        "local_notes": notes,
        "ready_to_run": (
            api_key_configured and provider_key_configured and notes_ready and config_ready
        ),
    }


class ProductRAGSmoke:
    def __init__(
        self,
        api_base: str,
        api_key: str,
        timeout: int,
        require_source_hints: bool,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.require_source_hints = require_source_hints
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

    @staticmethod
    def validate_health(health: dict[str, Any]) -> None:
        rag = health.get("rag", {})
        provider = rag.get("provider", {})
        failures = []
        if health.get("status") != "ready" or rag.get("ready") is not True:
            failures.append(f"RAG is not ready: {health.get('status')}")
        if provider.get("name") != "bailian":
            failures.append(f"provider is not bailian: {provider.get('name')}")
        if provider.get("llm_model") != "qwen3.6-plus":
            failures.append(f"llm_model is not qwen3.6-plus: {provider.get('llm_model')}")
        if provider.get("thinking_enabled") is not False:
            failures.append("Bailian thinking is not disabled")
        if provider.get("embedding_model") != "text-embedding-v4":
            failures.append(
                f"embedding_model is not text-embedding-v4: "
                f"{provider.get('embedding_model')}"
            )
        if failures:
            raise AssertionError("; ".join(failures))

    def rebuild_index(self) -> dict[str, Any]:
        response = self.request("POST", "/rag/rebuild")
        response.raise_for_status()
        return response.json()

    @staticmethod
    def validate_rebuild(rebuild: dict[str, Any]) -> None:
        failures = []
        if rebuild.get("failed_count", 0) != 0:
            failures.append(f"failed_count={rebuild.get('failed_count')}")
        if rebuild.get("indexed_count", 0) <= 0:
            failures.append("indexed_count is 0")
        if rebuild.get("status") not in {"complete", "success"}:
            failures.append(f"status={rebuild.get('status')}")
        if failures:
            raise AssertionError("; ".join(failures))

    def query(self, item: dict[str, Any]) -> dict[str, Any]:
        query = str(item["query"])
        source_hint = str(item["source_hint"])
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
        answer_contains_any = [
            str(value).strip()
            for value in item.get("answer_contains_any", [])
            if str(value).strip()
        ]
        answer_contains_all = [
            str(value).strip()
            for value in item.get("answer_contains_all", [])
            if str(value).strip()
        ]
        contains_any_ok = (
            True
            if not answer_contains_any
            else any(value.lower() in answer.lower() for value in answer_contains_any)
        )
        contains_all_ok = all(value.lower() in answer.lower() for value in answer_contains_all)
        failure_reasons = []
        if not answer:
            failure_reasons.append("empty_answer")
        if data.get("mock"):
            failure_reasons.append("mock_response")
        if "[Mock]" in answer:
            failure_reasons.append("mock_marker_in_answer")
        if not sources:
            failure_reasons.append("missing_sources")
        if self.require_source_hints and not hinted:
            failure_reasons.append("source_hint_not_found")
        if not contains_any_ok:
            failure_reasons.append("answer_missing_any_expected_term")
        if not contains_all_ok:
            failure_reasons.append("answer_missing_required_terms")

        result = {
            "id": item.get("id"),
            "category": item.get("category"),
            "query": query,
            "source_hint": source_hint,
            "elapsed_ms": elapsed_ms,
            "answer_chars": len(answer),
            "sources_count": len(sources),
            "source_titles": source_titles,
            "hinted_source_found": hinted,
            "answer_contains_any_ok": contains_any_ok,
            "answer_contains_all_ok": contains_all_ok,
            "failure_reasons": failure_reasons,
            "mock": bool(data.get("mock")),
            "passed": len(failure_reasons) == 0,
        }
        self.results.append(result)
        return result

    def run(self, queries: list[dict[str, str]]) -> dict[str, Any]:
        health = self.check_health()
        self.validate_health(health)
        rebuild = self.rebuild_index()
        self.validate_rebuild(rebuild)

        for item in queries:
            self.query(item)

        passed = sum(1 for item in self.results if item["passed"])
        hinted = sum(1 for item in self.results if item["hinted_source_found"])
        latencies = [item["elapsed_ms"] for item in self.results]
        categories: dict[str, dict[str, int]] = {}
        for item in self.results:
            category = item.get("category") or "uncategorized"
            current = categories.setdefault(category, {"total": 0, "passed": 0})
            current["total"] += 1
            if item["passed"]:
                current["passed"] += 1
        return {
            "timestamp": datetime.now().isoformat(),
            "health": health,
            "rebuild": rebuild,
            "summary": {
                "total_queries": len(self.results),
                "passed": passed,
                "hinted_source_found": hinted,
                "all_passed": passed == len(self.results),
                "average_latency_ms": (
                    round(sum(latencies) / len(latencies), 2) if latencies else None
                ),
                "max_latency_ms": max(latencies) if latencies else None,
                "categories": categories,
            },
            "results": self.results,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default=os.getenv("API_BASE", "http://127.0.0.1:8000/api"))
    parser.add_argument("--api-key", default=os.getenv("SECOND_BRAIN_API_KEY", ""))
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--report")
    parser.add_argument("--queries", help="Path to a JSON RAG quality query set")
    parser.add_argument(
        "--allow-missing-source-hints",
        action="store_true",
        help="Do not fail when source_hint is absent from retrieved titles.",
    )
    args = parser.parse_args()

    if args.preflight:
        report = build_preflight_report(args.api_key)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ready_to_run"] else 1

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        raise SystemExit("SECOND_BRAIN_API_KEY or --api-key is required")

    suite = ProductRAGSmoke(
        args.api_base,
        api_key,
        args.timeout,
        require_source_hints=not args.allow_missing_source_hints,
    )
    report = suite.run(load_queries(args.queries or ""))
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.report:
        path = Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0 if report["summary"]["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
