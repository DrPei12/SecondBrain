"""
Small JSON-backed vector store for product-grade local RAG.

This is deliberately simple: it keeps the current SecondBrain deployment
self-contained while preserving a clear boundary for replacing the store with
Chroma, pgvector, or a managed vector database later.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any


_DATE_TOKEN_RE = re.compile(r"\d{4}-\d{2}-\d{2}(?:-\d{4})?")
_WORD_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_.:+-]{2,}")


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for a, b in zip(left, right):
        dot += a * b
        left_norm += a * a
        right_norm += b * b
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (math.sqrt(left_norm) * math.sqrt(right_norm))


def _clip_relevance(score: float) -> float:
    return max(0.0, min(1.0, (score + 1.0) / 2.0))


def _lexical_score(query_text: str, chunk: dict[str, Any]) -> float:
    """Small exact-match boost for titles, dates, and product identifiers."""
    if not query_text:
        return 0.0

    query = query_text.casefold()
    title = str(chunk.get("title") or "").casefold()
    text = str(chunk.get("text") or "").casefold()
    score = 0.0

    for token in set(_DATE_TOKEN_RE.findall(query)):
        if token in title:
            score += 0.35
        elif token in text:
            score += 0.12

    for token in set(_WORD_TOKEN_RE.findall(query)):
        token = token.casefold()
        if token in title:
            score += 0.12
        elif token in text:
            score += 0.03

    if title and title in query:
        score += 0.25

    return min(score, 0.75)


def _modalities_from_tags(tags: list[str] | None) -> list[str]:
    modalities = []
    for tag in tags or []:
        value = str(tag).strip()
        if value.lower().startswith("modality:"):
            modality = value.split(":", 1)[1].strip().lower()
            if modality:
                modalities.append(modality)
    return sorted(set(modalities)) or ["text"]


def chunk_note_text(
    title: str,
    content: str,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Split note text into stable overlapping chunks."""
    text = f"# {title}\n\n{content or ''}".strip()
    if not text:
        return []

    chunk_size = max(400, chunk_size)
    chunk_overlap = max(0, min(chunk_overlap, chunk_size // 2))

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - chunk_overlap
    return chunks


class JsonVectorStore:
    """Persistent chunk store with cosine search."""

    def __init__(self, path: str, *, embedding_model: str, dimensions: int) -> None:
        self.path = Path(path)
        self.embedding_model = embedding_model
        self.dimensions = dimensions
        self._data: dict[str, Any] = {
            "version": 1,
            "embedding_model": embedding_model,
            "embedding_dimensions": dimensions,
            "chunks": [],
        }

    def load(self) -> None:
        if not self.path.exists():
            self.save()
            return

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if (
            raw.get("embedding_model") != self.embedding_model
            or int(raw.get("embedding_dimensions", 0)) != self.dimensions
        ):
            self.reset()
            return
        self._data = raw
        self._data.setdefault("chunks", [])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def reset(self) -> None:
        self._data = {
            "version": 1,
            "embedding_model": self.embedding_model,
            "embedding_dimensions": self.dimensions,
            "chunks": [],
            "reset_at": datetime.utcnow().isoformat(),
        }
        self.save()

    def upsert_note(
        self,
        *,
        note_id: str,
        title: str,
        content: str,
        tags: list[str] | None,
        source_url: str | None,
        chunk_size: int,
        chunk_overlap: int,
        embeddings: list[list[float]],
    ) -> int:
        chunks = chunk_note_text(
            title,
            content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        if len(chunks) != len(embeddings):
            raise ValueError("Chunk and embedding counts do not match")

        self.delete_note(note_id, save=False)
        now = datetime.utcnow().isoformat()
        modalities = _modalities_from_tags(tags)
        primary_modality = modalities[0] if len(modalities) == 1 else "mixed"
        for index, (text, embedding) in enumerate(zip(chunks, embeddings)):
            self._data["chunks"].append(
                {
                    "id": f"note_{note_id}_chunk_{index}",
                    "note_id": note_id,
                    "title": title,
                    "text": text,
                    "tags": tags or [],
                    "modality": primary_modality,
                    "modalities": modalities,
                    "source_url": source_url,
                    "chunk_index": index,
                    "embedding": embedding,
                    "indexed_at": now,
                }
            )
        self.save()
        return len(chunks)

    def delete_note(self, note_id: str, *, save: bool = True) -> int:
        before = len(self._data.get("chunks", []))
        self._data["chunks"] = [
            chunk
            for chunk in self._data.get("chunks", [])
            if chunk.get("note_id") != note_id
        ]
        removed = before - len(self._data["chunks"])
        if save and removed:
            self.save()
        return removed

    def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int,
        query_text: str = "",
    ) -> list[dict[str, Any]]:
        scored: list[dict[str, Any]] = []
        for chunk in self._data.get("chunks", []):
            embedding = chunk.get("embedding") or []
            vector_score = _cosine_similarity(query_embedding, embedding)
            lexical_score = _lexical_score(query_text, chunk)
            score = vector_score + lexical_score
            scored.append(
                {
                    "id": chunk["id"],
                    "note_id": chunk["note_id"],
                    "title": chunk.get("title") or "Untitled",
                    "snippet": chunk.get("text", "")[:700],
                    "text": chunk.get("text", ""),
                    "tags": chunk.get("tags") or [],
                    "modality": chunk.get("modality") or "text",
                    "modalities": chunk.get("modalities") or [chunk.get("modality") or "text"],
                    "source_url": chunk.get("source_url"),
                    "chunk_index": chunk.get("chunk_index", 0),
                    "score": score,
                    "vector_score": vector_score,
                    "lexical_score": lexical_score,
                    "relevance": _clip_relevance(score),
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def stats(self) -> dict[str, Any]:
        chunks = self._data.get("chunks", [])
        note_ids = {chunk.get("note_id") for chunk in chunks if chunk.get("note_id")}
        file_stat = self.path.stat() if self.path.exists() else None
        return {
            "path": str(self.path),
            "embedding_model": self.embedding_model,
            "embedding_dimensions": self.dimensions,
            "chunk_count": len(chunks),
            "document_count": len(note_ids),
            "exists": self.path.exists(),
            "file_size_bytes": file_stat.st_size if file_stat else 0,
            "updated_at": (
                datetime.utcfromtimestamp(file_stat.st_mtime).isoformat()
                if file_stat
                else None
            ),
        }
