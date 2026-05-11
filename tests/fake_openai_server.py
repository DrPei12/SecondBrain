#!/usr/bin/env python3
"""Tiny OpenAI-compatible fake server for offline RAG release smoke tests."""
from __future__ import annotations

import argparse
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


def embed_text(text: str, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    for token in text.lower().split()[:600]:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
        index = int.from_bytes(digest, "big") % dimensions
        vector[index] += 1.0
    for char in text[:8000]:
        if char.isspace():
            continue
        index = ord(char) % dimensions
        vector[index] += 0.25
    return vector


class FakeOpenAIHandler(BaseHTTPRequestHandler):
    server_version = "SecondBrainFakeOpenAI/1.0"

    def _json_response(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json()
            if self.path.endswith("/embeddings"):
                dimensions = min(int(payload.get("dimensions") or 1024), 64)
                inputs = payload.get("input") or []
                if isinstance(inputs, str):
                    inputs = [inputs]
                data = [
                    {
                        "object": "embedding",
                        "index": index,
                        "embedding": embed_text(str(text), dimensions),
                    }
                    for index, text in enumerate(inputs)
                ]
                self._json_response(
                    {
                        "object": "list",
                        "model": payload.get("model", "fake-embedding"),
                        "data": data,
                        "usage": {"prompt_tokens": 0, "total_tokens": 0},
                    }
                )
                return

            if self.path.endswith("/chat/completions"):
                messages = payload.get("messages") or []
                question = ""
                if messages:
                    question = str(messages[-1].get("content", "")).split("Notes:", 1)[0]
                self._json_response(
                    {
                        "id": "fake-chatcmpl",
                        "object": "chat.completion",
                        "model": payload.get("model", "fake-chat"),
                        "choices": [
                            {
                                "index": 0,
                                "finish_reason": "stop",
                                "message": {
                                    "role": "assistant",
                                    "content": (
                                        "Fake provider grounded answer for release smoke. "
                                        f"{question.strip()} [1]"
                                    ),
                                },
                            }
                        ],
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    }
                )
                return

            self._json_response({"error": f"Unsupported path: {self.path}"}, status=404)
        except Exception as exc:  # pragma: no cover - defensive fake server guard
            self._json_response({"error": str(exc)}, status=500)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), FakeOpenAIHandler)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
