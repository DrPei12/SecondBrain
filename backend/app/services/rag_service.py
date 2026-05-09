"""
RAG Service integrating LightRAG from HKUDS

This service provides:
- Vector storage and retrieval
- LLM integration for Q&A
- Automatic note indexing
"""
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import hashlib

# LightRAG imports from HKUDS
# Note: sentence_transformers import can hang, so we use lazy loading
try:
    from lightrag import LightRAG, QueryParam
    from lightrag.utils import EmbeddingFunc
    from lightrag.llm.openai import openai_complete
    LIGHTRAG_AVAILABLE = True
    # Lazy load sentence_transformers to avoid hanging on import
    SentenceTransformer = None
    _st_import_attempted = False
except ImportError:
    LIGHTRAG_AVAILABLE = False
    LightRAG = None
    QueryParam = None
    EmbeddingFunc = None
    SentenceTransformer = None
    openai_complete = None


async def mock_llm_complete(
    prompt,
    system_prompt=None,
    history_messages=None,
    **kwargs
):
    """Mock LLM function for development/testing without API key"""
    return "[Mock LLM] This is a mock response. Configure OPENAI_API_KEY for real LLM features."


from app.core.config import settings


def _load_sentence_transformer():
    """Lazy load SentenceTransformer with timeout protection"""
    global SentenceTransformer, _st_import_attempted

    if _st_import_attempted:
        return SentenceTransformer

    if SentenceTransformer is not None:
        return SentenceTransformer

    _st_import_attempted = True
    try:
        import threading
        import time

        result = [None]
        exception = [None]

        def import_thread():
            try:
                from sentence_transformers import SentenceTransformer as ST
                result[0] = ST
            except Exception as e:
                exception[0] = e

        t = threading.Thread(target=import_thread)
        t.daemon = True
        t.start()
        t.join(timeout=10.0)  # 10 second timeout

        if t.is_alive():
            print("[RAG] ⚠️ SentenceTransformer import timed out, disabling embedding")
            return None

        if exception[0]:
            print(f"[RAG] ⚠️ SentenceTransformer import failed: {exception[0]}")
            return None

        SentenceTransformer = result[0]
        print("[RAG] ✅ SentenceTransformer loaded successfully")
        return SentenceTransformer

    except Exception as e:
        print(f"[RAG] ⚠️ Failed to load SentenceTransformer: {e}")
        return None


class RAGService:
    """
    RAG Service for knowledge base Q&A

    Uses HKUDS LightRAG for vector storage, retrieval, and LLM integration
    """

    def __init__(self):
        """Initialize RAG service with LightRAG"""
        self._lightrag: Optional[LightRAG] = None
        self._initialized = False
        self._working_dir = settings.RAG_WORKING_DIR
        self._lightrag_available = LIGHTRAG_AVAILABLE
        self._embedding_model = None
        self._degraded_reason: Optional[str] = None

        # Ensure working directory exists
        if self._lightrag_available:
            os.makedirs(self._working_dir, exist_ok=True)

    def _get_embedding_func(self):
        """Create embedding function using Sentence Transformers"""
        # Lazy load SentenceTransformer
        ST = _load_sentence_transformer()
        if not ST or not EmbeddingFunc:
            return None
        if self._embedding_model is None:
            print(f"[RAG] Loading Sentence Transformer model...")
            self._embedding_model = ST('all-MiniLM-L6-v2')
            print(f"[RAG] Model loaded successfully")

        async def embed_func(texts: list[str]):
            return await asyncio.to_thread(
                self._embedding_model.encode,
                texts,
                convert_to_numpy=True,
            )

        return EmbeddingFunc(
            embedding_dim=384,  # all-MiniLM-L6-v2 dimension
            func=embed_func,
            max_token_size=8192
        )

    def _get_lightrag(self) -> Optional[LightRAG]:
        """Get or create LightRAG instance with embedding function"""
        if not self._lightrag_available or LightRAG is None:
            return None
        if self._lightrag is None:
            # Lazy load embedding model
            ST = _load_sentence_transformer()
            if self._embedding_model is None and ST and EmbeddingFunc:
                print(f"[RAG] Loading Sentence Transformer model...")
                self._embedding_model = ST('all-MiniLM-L6-v2')
                print(f"[RAG] Model loaded successfully")

            if self._embedding_model is None or EmbeddingFunc is None:
                print("[RAG] ⚠️ Running without embedding model - vector search disabled")
                return None

            # Create direct callable embedding function
            async def embed_func(texts: list[str]):
                return await asyncio.to_thread(
                    self._embedding_model.encode,
                    texts,
                    convert_to_numpy=True,
                )

            # Wrap with EmbeddingFunc (LightRAG expects this object with .func attribute)
            embedding_wrapper = EmbeddingFunc(
                embedding_dim=384,  # all-MiniLM-L6-v2 dimension
                func=embed_func,
                max_token_size=8192
            )

            # Configure LLM model function if OpenAI API key is available
            llm_func = mock_llm_complete  # Default to mock
            llm_model_name = "mock-model"

            openai_api_key = os.getenv("OPENAI_API_KEY", "")
            if openai_api_key and openai_api_key != "your-api-key-here" and openai_complete:
                # Set OpenAI API key in environment for the llm module
                os.environ["OPENAI_API_KEY"] = openai_api_key
                llm_func = openai_complete
                llm_model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
                print(f"[RAG] ✅ Using OpenAI LLM: {llm_model_name}")
            else:
                print(f"[RAG] ⚠️  OPENAI_API_KEY not configured, using mock LLM (embedding-only mode)")

            print(f"[RAG] Initializing LightRAG with working_dir: {self._working_dir}")
            self._lightrag = LightRAG(
                working_dir=self._working_dir,
                embedding_func=embedding_wrapper,  # Pass EmbeddingFunc wrapper
                llm_model_func=llm_func,
                llm_model_name=llm_model_name
            )
            print(f"[RAG] ✅ LightRAG initialized successfully (LLM: {llm_model_name})")
        return self._lightrag

    async def initialize(self):
        """Initialize the RAG system"""
        if not self._initialized:
            if not self._lightrag_available:
                self._initialized = True
                self._degraded_reason = "LightRAG import failed"
                print(f"[RAG Service] LightRAG not available, running in mock mode")
                return

            # Load heavy sync dependencies off the event loop, then initialize async storages.
            lightrag_instance = await asyncio.to_thread(self._get_lightrag)
            if lightrag_instance and hasattr(lightrag_instance, "initialize_storages"):
                await lightrag_instance.initialize_storages()
            self._initialized = True
            self._degraded_reason = None if lightrag_instance else "Embedding model unavailable"
            print(f"[RAG Service] LightRAG initialized with working_dir: {self._working_dir}")

    def mark_degraded(self, reason: str):
        """Keep API endpoints available when startup RAG initialization fails."""
        self._lightrag = None
        self._initialized = True
        self._degraded_reason = reason

    def _ensure_initialized(self):
        """Ensure RAG is initialized before operations"""
        if not self._initialized:
            raise RuntimeError("RAG Service not initialized. Call initialize() first.")

    async def index_note(
        self,
        db: AsyncSession,
        note_id: str,
        title: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Index a single note into the RAG system
        """
        self._ensure_initialized()

        # If LightRAG is not available, return mock success
        if not self._lightrag_available or self._lightrag is None:
            from app.models.note import Note
            result = await db.execute(
                select(Note).where(Note.id == note_id)
            )
            note = result.scalar_one_or_none()
            if note:
                note.indexed_for_rag = "mock"
                await db.commit()
            return {"success": True, "note_id": note_id, "doc_id": f"note_{note_id}_mock", "mock": True}

        try:
            from app.models.note import Note

            # Check if note exists
            result = await db.execute(
                select(Note).where(Note.id == note_id)
            )
            note = result.scalar_one_or_none()

            if not note:
                return {"success": False, "error": "Note not found"}

            # Prepare content for indexing
            full_content = f"# {title}\n\n{content}" if content else title

            # Create a unique document ID
            doc_id = f"note_{note_id}"

            # Use LightRAG's async insert method to add document.
            await self._lightrag.ainsert(
                full_content,
                ids=doc_id,
            )

            # Mark as indexed
            note.indexed_for_rag = "indexed"
            await db.commit()

            print(f"[RAG] Indexed note {note_id}: {title[:50]}...")

            return {
                "success": True,
                "note_id": note_id,
                "doc_id": doc_id
            }

        except Exception as e:
            print(f"[RAG ERROR] Failed to index note {note_id}: {e}")

            # Mark as failed
            from app.models.note import Note
            result = await db.execute(
                select(Note).where(Note.id == note_id)
            )
            note = result.scalar_one_or_none()
            if note:
                note.indexed_for_rag = "failed"
                await db.commit()

            return {
                "success": False,
                "note_id": note_id,
                "error": str(e)
            }

    async def index_notes_batch(
        self,
        db: AsyncSession,
        note_ids: Optional[List[str]] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Batch index notes for RAG
        """
        self._ensure_initialized()

        from app.services.note_service import note_service

        # Get notes to index
        notes = await note_service.get_notes_for_rag_indexing(
            db, note_ids=note_ids, force=force
        )

        if not notes:
            return {
                "indexed_count": 0,
                "failed_count": 0,
                "status": "complete",
                "message": "No notes to index"
            }

        indexed_ids = []
        failed_ids = []

        for note in notes:
            result = await self.index_note(
                db,
                note_id=note.id,
                title=note.title,
                content=note.content or ""
            )

            if result.get("success"):
                indexed_ids.append(note.id)
            else:
                failed_ids.append(note.id)

        return {
            "indexed_count": len(indexed_ids),
            "failed_count": len(failed_ids),
            "status": "complete",
            "message": f"Indexed {len(indexed_ids)} notes, {len(failed_ids)} failed"
        }

    async def query(
        self,
        query_text: str,
        mode: str = "mix",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Query the RAG knowledge base

        Args:
            query_text: Natural language query
            mode: Query mode (local, global, hybrid, naive, mix, bypass)
            top_k: Number of results to retrieve

        Returns:
            Query result with answer and sources
        """
        self._ensure_initialized()

        # If LightRAG is not available, return mock response
        if not self._lightrag_available or self._lightrag is None:
            return {
                "query": query_text,
                "answer": f"[Mock] RAG query processed: {query_text}",
                "sources": [],
                "mode": mode,
                "mock": True
            }

        try:
            # Create query parameters
            if QueryParam is None:
                raise RuntimeError("QueryParam not available from lightrag")

            query_param = QueryParam(
                mode=mode,
                top_k=top_k
            )

            # Execute query using LightRAG's async query method.
            result = await self._lightrag.aquery(query_text, param=query_param)

            # LightRAG returns string answer
            return {
                "query": query_text,
                "answer": result if isinstance(result, str) else str(result),
                "sources": [],
                "mode": mode
            }

        except Exception as e:
            print(f"[RAG ERROR] Query failed: {e}")
            return {
                "query": query_text,
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "mode": mode,
                "error": str(e)
            }

    async def delete_document(self, note_id: str) -> bool:
        """
        Delete a document from RAG index
        """
        self._ensure_initialized()

        # If LightRAG is not available, return mock success
        if not self._lightrag_available or self._lightrag is None:
            return True

        try:
            doc_id = f"note_{note_id}"

            await self._lightrag.adelete_by_doc_id(doc_id)

            print(f"[RAG] Deleted document for note {note_id}")
            return True

        except Exception as e:
            print(f"[RAG ERROR] Failed to delete document for note {note_id}: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get RAG indexing statistics
        """
        self._ensure_initialized()

        try:
            stats = {
                "working_dir": self._working_dir,
                "initialized": self._initialized,
                "lightrag_available": self._lightrag_available,
                "lightrag_ready": self._lightrag is not None,
                "degraded_reason": self._degraded_reason,
            }

            # Try to get document count from working directory
            if os.path.exists(self._working_dir):
                file_count = len(list(Path(self._working_dir).glob("**/*")))
                stats["file_count"] = file_count

            return stats

        except Exception as e:
            print(f"[RAG ERROR] Failed to get stats: {e}")
            return {
                "error": str(e),
                "working_dir": self._working_dir,
                "initialized": self._initialized
            }

    async def close(self):
        """Cleanup RAG resources"""
        if self._lightrag:
            try:
                if hasattr(self._lightrag, 'finalize_storages'):
                    await self._lightrag.finalize_storages()
                elif hasattr(self._lightrag, 'close'):
                    await self._lightrag.close()
            except Exception as e:
                print(f"[RAG ERROR] Error closing: {e}")
            finally:
                self._lightrag = None
                self._initialized = False
                self._degraded_reason = None


# Singleton instance
rag_service = RAGService()
