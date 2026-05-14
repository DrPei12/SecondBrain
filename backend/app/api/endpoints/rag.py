"""
RAG API endpoints
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.schemas.note import NoteCreate
from app.services.rag_service import rag_service
from app.services.note_service import note_service
from app.services.multimodal_ingest import multimodal_ingestion_service
from app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGIndexRequest,
    RAGIndexResponse,
    RAGIngestResponse,
)


router = APIRouter()


def _parse_tags(tags: str | None) -> list[str]:
    values = []
    for tag in (tags or "").split(","):
        value = tag.strip()
        if value and value not in values:
            values.append(value)
    return values


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
    try:
        result = await rag_service.query(
            query_text=request.query,
            mode=request.mode,
            top_k=request.top_k
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG query failed: {exc}",
        ) from exc
    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result["error"],
        )
    
    return RAGQueryResponse(
        query=request.query,
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        mode=request.mode,
        engine=result.get("engine"),
        provider=result.get("provider"),
        elapsed_ms=result.get("elapsed_ms"),
        mock=result.get("mock", False),
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
        retry_count=result.get("retry_count", 0),
        status=result.get("status", "complete"),
        message=result.get("message", ""),
        indexed_ids=result.get("indexed_ids", []),
        failed_ids=result.get("failed_ids", []),
        errors=result.get("errors", {}),
    )


@router.post("/ingest", response_model=RAGIngestResponse)
async def ingest_multimodal_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    caption: str = Form(""),
    tags: str = Form(""),
    source_url: str = Form(""),
    index: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a file as a modality-aware note, then optionally index it for RAG.

    Supported extraction is intentionally layered:
    - text/markdown/html/json/code files become text chunks
    - csv/xlsx become markdown table chunks
    - pdf/docx/pptx use optional Python parsers when installed
    - images/audio/video store metadata and user captions for retrieval
    """
    try:
        document = await multimodal_ingestion_service.ingest_upload(
            file,
            title=title,
            caption=caption,
        )
    except ValueError as exc:
        status_code = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if "RAG_MAX_UPLOAD_BYTES" in str(exc)
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    note_tags = _parse_tags(tags)
    for tag in document.tags:
        if tag not in note_tags:
            note_tags.append(tag)

    note = await note_service.create_note(
        db,
        NoteCreate(
            title=document.title,
            content=document.content,
            tags=note_tags,
            source_url=source_url.strip() or document.source_url,
        ),
    )

    index_result = {}
    if index:
        try:
            index_result = await rag_service.index_note(
                db,
                note_id=note.id,
                title=note.title,
                content=note.content or "",
            )
        except RuntimeError as exc:
            index_result = {"success": False, "error": str(exc)}

    return RAGIngestResponse(
        note=note.to_dict(),
        indexed=bool(index_result.get("success")),
        index_result=index_result,
        document=document.response_metadata(),
    )


async def _add_note_index_counts(db: AsyncSession, stats: dict) -> dict:
    from app.models.note import Note

    result = await db.execute(
        select(Note.indexed_for_rag, func.count(Note.id)).group_by(Note.indexed_for_rag)
    )
    counts = {status_name or "unknown": count for status_name, count in result.all()}
    total_result = await db.execute(select(func.count(Note.id)))
    stats["notes"] = {
        "total": total_result.scalar() or 0,
        "by_rag_status": counts,
    }
    return stats


@router.get("/stats")
async def get_rag_stats(db: AsyncSession = Depends(get_db)):
    """Get RAG indexing statistics"""
    stats = await rag_service.get_index_stats()
    return await _add_note_index_counts(db, stats)


@router.get("/health")
async def get_rag_health(db: AsyncSession = Depends(get_db)):
    """Get RAG readiness, provider, and index health."""
    stats = await rag_service.get_index_stats()
    stats = await _add_note_index_counts(db, stats)
    status_text = "ready" if stats.get("ready") else "degraded"
    return {
        "status": status_text,
        **stats,
    }


@router.post("/document/{note_id}/reindex", response_model=RAGIndexResponse)
async def reindex_rag_document(
    note_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Reindex one note into RAG."""
    result = await rag_service.index_notes_batch(
        db,
        note_ids=[note_id],
        force=True,
    )
    return RAGIndexResponse(
        indexed_count=result.get("indexed_count", 0),
        failed_count=result.get("failed_count", 0),
        retry_count=result.get("retry_count", 0),
        status=result.get("status", "complete"),
        message=result.get("message", ""),
        indexed_ids=result.get("indexed_ids", []),
        failed_ids=result.get("failed_ids", []),
        errors=result.get("errors", {}),
    )


@router.post("/rebuild", response_model=RAGIndexResponse)
async def rebuild_rag_index(
    db: AsyncSession = Depends(get_db)
):
    """Force rebuild the complete RAG index from notes."""
    result = await rag_service.index_notes_batch(db, force=True)
    return RAGIndexResponse(
        indexed_count=result.get("indexed_count", 0),
        failed_count=result.get("failed_count", 0),
        retry_count=result.get("retry_count", 0),
        status=result.get("status", "complete"),
        message=result.get("message", ""),
        indexed_ids=result.get("indexed_ids", []),
        failed_ids=result.get("failed_ids", []),
        errors=result.get("errors", {}),
    )


@router.delete("/document/{note_id}")
async def delete_rag_document(
    note_id: str
):
    """Delete a document from RAG index"""
    deleted = await rag_service.delete_document(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": f"Document for note {note_id} deleted"}
