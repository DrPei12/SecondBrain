"""
RAG API endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.services.rag_service import rag_service
from app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGIndexRequest,
    RAGIndexResponse
)


router = APIRouter()


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Query the RAG knowledge base with natural language
    
    Example:
    {
        "query": "What are the key insights about AI from my notes?",
        "mode": "mix",
        "top_k": 10
    }
    """
    result = await rag_service.query(
        query_text=request.query,
        mode=request.mode,
        top_k=request.top_k
    )
    
    return RAGQueryResponse(
        query=request.query,
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        mode=request.mode
    )


@router.post("/index", response_model=RAGIndexResponse)
async def index_notes(
    request: RAGIndexRequest = None,
    force: bool = Query(False, description="Force reindexing"),
    db: AsyncSession = Depends(get_db)
):
    """
    Index notes for RAG retrieval
    
    If no note_ids provided, indexes all pending notes.
    """
    if request is None:
        request = RAGIndexRequest()
    
    result = await rag_service.index_notes_batch(
        db,
        note_ids=request.note_ids,
        force=request.force_reindex or force
    )
    
    return RAGIndexResponse(
        indexed_count=result.get("indexed_count", 0),
        failed_count=result.get("failed_count", 0),
        status=result.get("status", "complete"),
        message=result.get("message", "")
    )


@router.get("/stats")
async def get_rag_stats():
    """Get RAG indexing statistics"""
    stats = await rag_service.get_index_stats()
    return stats


@router.delete("/document/{note_id}")
async def delete_rag_document(
    note_id: str
):
    """Delete a document from RAG index"""
    deleted = await rag_service.delete_document(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": f"Document for note {note_id} deleted"}
