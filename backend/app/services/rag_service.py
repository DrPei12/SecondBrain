"""
Product RAG service for SecondBrain.

The primary path is a real OpenAI-compatible vector RAG pipeline:
notes -> chunks -> embeddings -> cosine retrieval -> grounded LLM answer.
LightRAG remains available as an optional engine for graph-enhanced indexing.
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.llm_provider import OpenAICompatibleProvider
from app.services.vector_store import JsonVectorStore, chunk_note_text

try:
    from lightrag import LightRAG, QueryParam
    from lightrag.utils import EmbeddingFunc

    LIGHTRAG_AVAILABLE = True
except ImportError:
    LightRAG = None
    QueryParam = None
    EmbeddingFunc = None
    LIGHTRAG_AVAILABLE = False


class RAGService:
    """RAG facade used by API routes, CLI, and note lifecycle hooks."""

    def __init__(self) -> None:
        self._initialized = False
        self._working_dir = settings.RAG_WORKING_DIR
        self._engine = settings.RAG_ENGINE.strip().lower() or "vector"
        self._provider: OpenAICompatibleProvider | None = None
        self._vector_store: JsonVectorStore | None = None
        self._lightrag: Optional[LightRAG] = None
        self._lightrag_available = LIGHTRAG_AVAILABLE
        self._degraded_reason: str | None = None
        self._lock = asyncio.Lock()
        self._recent_events: list[dict[str, Any]] = []
        self._last_index_job: dict[str, Any] | None = None
        self._index_metrics: dict[str, Any] = {
            "runs": 0,
            "indexed_total": 0,
            "failed_total": 0,
            "retry_total": 0,
            "last_duration_ms": None,
        }
        self._query_metrics: dict[str, Any] = {
            "count": 0,
            "failure_count": 0,
            "total_latency_ms": 0.0,
            "last_latency_ms": None,
            "last_query_at": None,
            "last_error": None,
        }

    @staticmethod
    def _now_iso() -> str:
        return datetime.utcnow().isoformat()

    def _append_event(self, event_type: str, status: str, detail: dict[str, Any]) -> None:
        self._recent_events.append(
            {
                "timestamp": self._now_iso(),
                "type": event_type,
                "status": status,
                "detail": detail,
            }
        )
        self._recent_events = self._recent_events[-20:]

    def _record_query_success(self, elapsed_ms: float) -> None:
        self._query_metrics["count"] += 1
        self._query_metrics["total_latency_ms"] += elapsed_ms
        self._query_metrics["last_latency_ms"] = elapsed_ms
        self._query_metrics["last_query_at"] = self._now_iso()
        self._query_metrics["last_error"] = None

    def _record_query_failure(self, started: float, error: Exception) -> None:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        self._query_metrics["failure_count"] += 1
        self._query_metrics["last_latency_ms"] = elapsed_ms
        self._query_metrics["last_query_at"] = self._now_iso()
        self._query_metrics["last_error"] = str(error)
        self._append_event(
            "query",
            "failed",
            {"elapsed_ms": elapsed_ms, "error": str(error)},
        )

    async def initialize(self) -> None:
        """Initialize provider, local vector store, and optional LightRAG."""
        if self._initialized:
            return

        os.makedirs(self._working_dir, exist_ok=True)
        self._provider = OpenAICompatibleProvider()
        self._vector_store = JsonVectorStore(
            settings.RAG_VECTOR_STORE_FILE,
            embedding_model=self._provider.status.embedding_model,
            dimensions=self._provider.status.embedding_dimensions,
        )
        self._vector_store.load()

        if not self._provider.configured:
            self._degraded_reason = (
                "Model provider is not configured; set DASHSCOPE_API_KEY for "
                "Bailian or OPENAI_API_KEY for OpenAI"
            )
        else:
            self._degraded_reason = None

        if self._engine in {"lightrag", "hybrid"}:
            await self._initialize_lightrag()

        self._initialized = True

    async def _initialize_lightrag(self) -> None:
        if not self._provider or not self._provider.configured:
            return
        if not self._lightrag_available or LightRAG is None or EmbeddingFunc is None:
            self._degraded_reason = "LightRAG is not installed"
            return

        async def embed_func(texts: list[str]):
            embeddings = await self._provider.embed_texts(texts)
            try:
                import numpy as np

                return np.array(embeddings, dtype="float32")
            except Exception:
                return embeddings

        async def llm_func(
            prompt: str,
            system_prompt: str | None = None,
            history_messages: list[dict[str, str]] | None = None,
            **_: Any,
        ) -> str:
            messages: list[dict[str, str]] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.extend(history_messages or [])
            messages.append({"role": "user", "content": prompt})
            return await self._provider.chat(messages, temperature=0.0)

        try:
            embedding_wrapper = EmbeddingFunc(
                embedding_dim=self._provider.status.embedding_dimensions,
                func=embed_func,
                max_token_size=8192,
                model_name=self._provider.status.embedding_model,
            )
            self._lightrag = LightRAG(
                working_dir=self._working_dir,
                embedding_func=embedding_wrapper,
                llm_model_func=llm_func,
                llm_model_name=self._provider.status.llm_model,
            )
            if hasattr(self._lightrag, "initialize_storages"):
                await self._lightrag.initialize_storages()
        except Exception as exc:
            self._lightrag = None
            self._degraded_reason = f"LightRAG initialization failed: {exc}"

    def mark_degraded(self, reason: str) -> None:
        """Keep API endpoints alive while reporting a real not-ready state."""
        self._initialized = True
        self._degraded_reason = reason

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError("RAG Service not initialized. Call initialize() first.")

    def _ensure_ready(self) -> None:
        self._ensure_initialized()
        if not self._provider or not self._provider.configured:
            provider = self._provider.status.provider if self._provider else "unknown"
            raise RuntimeError(f"RAG model provider is not configured: {provider}")
        if not self._vector_store:
            raise RuntimeError("RAG vector store is not initialized")

    async def index_note(
        self,
        db: AsyncSession,
        note_id: str,
        title: str,
        content: str,
    ) -> dict[str, Any]:
        """Index one note into the local vector store and optional LightRAG."""
        self._ensure_initialized()

        from app.models.note import Note

        result = await db.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()
        if not note:
            return {"success": False, "note_id": note_id, "error": "Note not found"}

        if not self._provider or not self._provider.configured or not self._vector_store:
            note.indexed_for_rag = "pending"
            await db.commit()
            return {
                "success": False,
                "note_id": note_id,
                "error": self._degraded_reason or "RAG provider is not configured",
            }

        try:
            note.indexed_for_rag = "indexing"
            await db.commit()

            chunks = chunk_note_text(
                title,
                content or "",
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            )
            if not chunks:
                raise RuntimeError("Note has no indexable content")

            embeddings = await self._provider.embed_texts(chunks)

            async with self._lock:
                chunk_count = self._vector_store.upsert_note(
                    note_id=note_id,
                    title=title,
                    content=content or "",
                    tags=note.tags or [],
                    source_url=note.source_url,
                    chunk_size=settings.RAG_CHUNK_SIZE,
                    chunk_overlap=settings.RAG_CHUNK_OVERLAP,
                    embeddings=embeddings,
                )

            lightrag_warning: str | None = None
            if self._lightrag is not None:
                try:
                    await self._lightrag.ainsert(
                        f"# {title}\n\n{content or ''}",
                        ids=f"note_{note_id}",
                    )
                except Exception as exc:
                    lightrag_warning = str(exc)

            note.indexed_for_rag = "indexed"
            await db.commit()
            return {
                "success": True,
                "note_id": note_id,
                "doc_id": f"note_{note_id}",
                "chunk_count": chunk_count,
                "lightrag_warning": lightrag_warning,
                "mock": False,
            }
        except Exception as exc:
            note.indexed_for_rag = "failed"
            await db.commit()
            return {
                "success": False,
                "note_id": note_id,
                "error": str(exc),
                "mock": False,
            }

    async def index_notes_batch(
        self,
        db: AsyncSession,
        note_ids: Optional[list[str]] = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Index pending notes or a requested note set."""
        self._ensure_initialized()
        started = time.perf_counter()
        job_id = f"rag-index-{int(started * 1000)}"
        retry_limit = max(0, settings.RAG_INDEX_RETRIES)
        self._last_index_job = {
            "id": job_id,
            "status": "running",
            "started_at": self._now_iso(),
            "force": force,
            "requested_note_count": len(note_ids) if note_ids else None,
            "retry_limit": retry_limit,
        }

        from app.services.note_service import note_service

        provider_ready = bool(self._provider and self._provider.configured)
        if force and not note_ids and self._vector_store and provider_ready:
            async with self._lock:
                self._vector_store.reset()

        notes = await note_service.get_notes_for_rag_indexing(
            db,
            note_ids=note_ids,
            force=force,
        )
        if not notes:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            self._last_index_job.update(
                {
                    "status": "complete",
                    "ended_at": self._now_iso(),
                    "duration_ms": elapsed_ms,
                    "indexed_count": 0,
                    "failed_count": 0,
                    "retry_count": 0,
                }
            )
            self._append_event(
                "index",
                "complete",
                {"job_id": job_id, "indexed_count": 0, "failed_count": 0},
            )
            return {
                "indexed_count": 0,
                "failed_count": 0,
                "retry_count": 0,
                "indexed_ids": [],
                "failed_ids": [],
                "status": "complete",
                "message": "No notes to index",
            }

        indexed_ids: list[str] = []
        failed_ids: list[str] = []
        errors: dict[str, str] = {}
        retry_count = 0

        for note in notes:
            result: dict[str, Any] = {}
            for attempt in range(retry_limit + 1):
                result = await self.index_note(
                    db,
                    note_id=note.id,
                    title=note.title,
                    content=note.content or "",
                )
                if result.get("success"):
                    break
                if attempt < retry_limit:
                    retry_count += 1
                    await asyncio.sleep(min(2**attempt, 2))
            if result.get("success"):
                indexed_ids.append(note.id)
            else:
                failed_ids.append(note.id)
                errors[note.id] = result.get("error", "Unknown indexing error")

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        status_text = "complete" if not failed_ids else "partial"
        self._last_index_job.update(
            {
                "status": status_text,
                "ended_at": self._now_iso(),
                "duration_ms": elapsed_ms,
                "indexed_count": len(indexed_ids),
                "failed_count": len(failed_ids),
                "retry_count": retry_count,
                "errors": errors,
            }
        )
        self._index_metrics["runs"] += 1
        self._index_metrics["indexed_total"] += len(indexed_ids)
        self._index_metrics["failed_total"] += len(failed_ids)
        self._index_metrics["retry_total"] += retry_count
        self._index_metrics["last_duration_ms"] = elapsed_ms
        self._append_event(
            "index",
            status_text,
            {
                "job_id": job_id,
                "indexed_count": len(indexed_ids),
                "failed_count": len(failed_ids),
                "retry_count": retry_count,
                "duration_ms": elapsed_ms,
            },
        )

        return {
            "indexed_count": len(indexed_ids),
            "failed_count": len(failed_ids),
            "retry_count": retry_count,
            "indexed_ids": indexed_ids,
            "failed_ids": failed_ids,
            "errors": errors,
            "status": status_text,
            "message": f"Indexed {len(indexed_ids)} notes, {len(failed_ids)} failed",
        }

    async def query(
        self,
        query_text: str,
        mode: str = "mix",
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Query the indexed knowledge base and return grounded sources."""
        started = time.perf_counter()
        try:
            self._ensure_ready()
            assert self._provider is not None
            assert self._vector_store is not None

            query_embedding = (await self._provider.embed_texts([query_text]))[0]
            matches = self._vector_store.search(
                query_embedding,
                top_k=top_k,
                query_text=query_text,
            )

            if not matches:
                elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
                self._record_query_success(elapsed_ms)
                self._append_event(
                    "query",
                    "empty",
                    {"elapsed_ms": elapsed_ms, "top_k": top_k},
                )
                return {
                    "query": query_text,
                    "answer": "No relevant indexed notes were found for this question.",
                    "sources": [],
                    "mode": mode,
                    "engine": self._engine,
                    "provider": self._provider.status.provider,
                    "elapsed_ms": elapsed_ms,
                    "mock": False,
                }

            context = "\n\n".join(
                f"[{idx}] {item['title']} "
                f"(note_id={item['note_id']}, modalities={', '.join(item.get('modalities') or [])})"
                f"\n{item['text']}"
                for idx, item in enumerate(matches, 1)
            )
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are SecondBrain RAG. Answer only from the provided "
                        "notes. If the notes are insufficient, say what is missing. "
                        "Cite sources inline like [1], [2]."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question:\n{query_text}\n\nNotes:\n{context}",
                },
            ]
            answer = await self._provider.chat(messages, temperature=0.1)

            sources = [
                {
                    "id": item["note_id"],
                    "note_id": item["note_id"],
                    "chunk_id": item["id"],
                    "title": item["title"],
                    "snippet": item["snippet"],
                    "modality": item.get("modality"),
                    "modalities": item.get("modalities") or [],
                    "relevance": item["relevance"],
                    "score": item["score"],
                    "chunk_index": item["chunk_index"],
                    "source_url": item["source_url"],
                }
                for item in matches
            ]

            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            self._record_query_success(elapsed_ms)
            self._append_event(
                "query",
                "complete",
                {"elapsed_ms": elapsed_ms, "sources_count": len(sources), "top_k": top_k},
            )
            return {
                "query": query_text,
                "answer": answer,
                "sources": sources,
                "mode": mode,
                "engine": self._engine,
                "provider": self._provider.status.provider,
                "elapsed_ms": elapsed_ms,
                "mock": False,
            }
        except Exception as exc:
            self._record_query_failure(started, exc)
            raise

    async def delete_document(self, note_id: str) -> bool:
        """Delete a note from vector and optional LightRAG indexes."""
        self._ensure_initialized()
        removed = 0
        if self._vector_store:
            async with self._lock:
                removed = self._vector_store.delete_note(note_id)

        if self._lightrag is not None:
            try:
                await self._lightrag.adelete_by_doc_id(f"note_{note_id}")
            except Exception:
                pass

        return removed > 0 or self._lightrag is not None

    async def get_index_stats(self) -> dict[str, Any]:
        """Return real readiness and index statistics."""
        self._ensure_initialized()
        provider_status = self._provider.status if self._provider else None
        stats: dict[str, Any] = {
            "working_dir": self._working_dir,
            "engine": self._engine,
            "initialized": self._initialized,
            "ready": bool(self._provider and self._provider.configured and self._vector_store),
            "degraded_reason": self._degraded_reason,
            "mock": False,
            "lightrag_available": self._lightrag_available,
            "lightrag_ready": self._lightrag is not None,
            "operations": {
                "last_index_job": self._last_index_job,
                "recent_events": self._recent_events,
            },
            "metrics": {
                "index": self._index_metrics,
                "query": {
                    **self._query_metrics,
                    "average_latency_ms": (
                        round(
                            self._query_metrics["total_latency_ms"]
                            / self._query_metrics["count"],
                            2,
                        )
                        if self._query_metrics["count"]
                        else None
                    ),
                },
                "cost": {
                    "available": False,
                    "reason": "Provider token usage is not returned by the current wrapper",
                },
            },
        }
        if provider_status:
            stats["provider"] = {
                "name": provider_status.provider,
                "configured": provider_status.configured,
                "base_url": provider_status.base_url,
                "llm_model": provider_status.llm_model,
                "embedding_model": provider_status.embedding_model,
                "embedding_dimensions": provider_status.embedding_dimensions,
                "thinking_enabled": provider_status.thinking_enabled,
            }
        if self._vector_store:
            stats["vector_store"] = self._vector_store.stats()
        if os.path.exists(self._working_dir):
            stats["working_dir_file_count"] = len(list(Path(self._working_dir).glob("**/*")))
        return stats

    async def close(self) -> None:
        if self._lightrag:
            try:
                if hasattr(self._lightrag, "finalize_storages"):
                    await self._lightrag.finalize_storages()
                elif hasattr(self._lightrag, "close"):
                    await self._lightrag.close()
            finally:
                self._lightrag = None
        self._initialized = False


rag_service = RAGService()
