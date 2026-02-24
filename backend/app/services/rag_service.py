"""
RAG Service integrating LightRAG from RAG-Anything

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

# LightRAG imports from RAG-Anything
try:
    from lightrag import LightRAG
    from lightrag.utils import logger
    from lightrag import QueryParam
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    LightRAG = None
    QueryParam = None
    logger = None

# Simple logger wrapper
def _log_info(msg):
    if logger:
        _log_info(msg)
    else:
        print(f"[INFO] {msg}")

def _log_error(msg):
    if logger:
        _log_error(msg)
    else:
        print(f"[ERROR] {msg}")

from app.core.config import settings


class RAGService:
    """
    RAG Service for knowledge base Q&A
    
    Reuses vector storage, retrieval, and LLM call logic from RAG-Anything
    """
    
    def __init__(self):
        """Initialize RAG service with LightRAG"""
        self._lightrag: Optional[object] = None
        self._initialized = False
        self._working_dir = settings.RAG_WORKING_DIR
        self._lightrag_available = LIGHTRAG_AVAILABLE
        
        # Ensure working directory exists
        if self._lightrag_available:
            os.makedirs(self._working_dir, exist_ok=True)
    
    def _get_lightrag(self) -> Optional[LightRAG]:
        """Get or create LightRAG instance"""
        if not self._lightrag_available or LightRAG is None:
            return None
        if self._lightrag is None:
            self._lightrag = LightRAG(
                working_dir=self._working_dir,
                # LightRAG will use default settings
                # Can be customized with kwargs if needed
            )
        return self._lightrag
    
    async def initialize(self):
        """Initialize the RAG system"""
        if not self._initialized:
            if not self._lightrag_available:
                self._initialized = True
                print(f"[RAG Service] LightRAG not available, running in mock mode")
                return
            # Run in executor for sync LightRAG initialization
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._get_lightrag)
            self._initialized = True
            if logger:
                _log_info(f"RAG Service initialized with working_dir: {self._working_dir}")
    
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
        
        Args:
            db: Database session
            note_id: Note ID
            title: Note title
            content: Note content (Markdown)
            
        Returns:
            Indexing result dict
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
            # Combine title and content
            full_content = f"# {title}\n\n{content}" if content else title
            
            # Create a unique document ID
            doc_id = f"note_{note_id}"
            
            # Use LightRAG's upsert method to add/update document
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self._lightrag.upsert(
                    full_content,
                    ids=doc_id,
                    extra_info={"note_id": note_id, "title": title}
                )
            )
            
            # Mark as indexed
            note.indexed_for_rag = "indexed"
            await db.commit()
            
            _log_info(f"Indexed note {note_id}: {title[:50]}...")
            
            return {
                "success": True,
                "note_id": note_id,
                "doc_id": doc_id
            }
            
        except Exception as e:
            _log_error(f"Failed to index note {note_id}: {e}")
            
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
        
        Args:
            db: Database session
            note_ids: Specific note IDs (None = all pending)
            force: Force reindexing of already indexed notes
            
        Returns:
            Indexing results summary
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
            
            # Execute query
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._lightrag.aquery(query_text, param=query_param)
            )
            
            # Extract sources if available
            # LightRAG may return sources in the result metadata
            sources = []
            if hasattr(result, 'metadata'):
                sources = result.metadata.get('sources', [])
            
            return {
                "query": query_text,
                "answer": result if isinstance(result, str) else str(result),
                "sources": sources,
                "mode": mode
            }
            
        except Exception as e:
            _log_error(f"RAG query failed: {e}")
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
        
        Args:
            note_id: Note ID to delete
            
        Returns:
            True if successful
        """
        self._ensure_initialized()
        
        # If LightRAG is not available, return mock success
        if not self._lightrag_available or self._lightrag is None:
            return True
        
        try:
            doc_id = f"note_{note_id}"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._lightrag.delete(doc_id)
            )
            
            _log_info(f"Deleted document for note {note_id}")
            return True
            
        except Exception as e:
            _log_error(f"Failed to delete document for note {note_id}: {e}")
            return False
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get RAG indexing statistics
        
        Returns:
            Statistics about the indexed knowledge base
        """
        self._ensure_initialized()
        
        try:
            # LightRAG may have methods to get stats
            stats = {
                "working_dir": self._working_dir,
                "initialized": self._initialized,
            }
            
            # Try to get document count if method exists
            if hasattr(self._lightrag, 'get_stats'):
                stats.update(self._lightrag.get_stats())
            
            return stats
            
        except Exception as e:
            _log_error(f"Failed to get RAG stats: {e}")
            return {
                "error": str(e),
                "working_dir": self._working_dir,
                "initialized": self._initialized
            }
    
    async def close(self):
        """Cleanup RAG resources"""
        if self._lightrag:
            try:
                # LightRAG may have cleanup methods
                if hasattr(self._lightrag, 'close'):
                    await self._lightrag.close()
            except Exception as e:
                _log_error(f"Error closing RAG: {e}")
            finally:
                self._lightrag = None
                self._initialized = False


# Singleton instance
rag_service = RAGService()
