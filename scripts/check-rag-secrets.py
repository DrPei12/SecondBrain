#!/usr/bin/env python3
"""Scan tracked files for likely provider secrets without printing secret values."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


PATTERNS = [
    ("generic_sk_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{20,}\b")),
    ("dashscope_env_value", re.compile(r"(DASHSCOPE_API_KEY|BAILIAN_API_KEY)\s*=\s*['\"]?[^'\"\s#]{12,}", re.I)),
]

ALLOWLIST_MARKERS = (
    "sk-REPLACE",
    "sk-test",
    "sk_xxx",
    "<your",
    "example",
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [Path(line) for line in result.stdout.splitlines() if line.strip()]


def scan_file(path: Path) -> list[tuple[int, str]]:
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc"}:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    findings: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        normalized = line.lower()
        if any(marker.lower() in normalized for marker in ALLOWLIST_MARKERS):
            continue
        for name, pattern in PATTERNS:
            if pattern.search(line):
                findings.append((line_number, name))
    return findings


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        for line_number, pattern_name in scan_file(path):
            findings.append(f"{path}:{line_number}: {pattern_name}")

    if findings:
        print("Potential tracked secret material found; values are intentionally hidden.")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("No likely provider secrets found in tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
