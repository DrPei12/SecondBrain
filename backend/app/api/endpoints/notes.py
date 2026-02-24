"""
Notes API endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.services.note_service import note_service
from app.schemas.note import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
    NoteFilter,
    BatchNoteCreate,
    BatchNoteResponse
)


router = APIRouter()


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new note"""
    note = await note_service.create_note(db, note_data)
    return note


@router.post("/batch", response_model=BatchNoteResponse)
async def create_notes_batch(
    batch_data: BatchNoteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create multiple notes in batch (for AI agents)"""
    created, failed = await note_service.create_notes_batch(db, batch_data.notes)
    return BatchNoteResponse(
        created=[note.to_dict() for note in created],
        failed=failed,
        total_created=len(created),
        total_failed=len(failed)
    )


@router.get("/", response_model=NoteListResponse)
async def list_notes(
    status: Optional[str] = Query(None, description="Filter by status"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List notes with optional filters"""
    filters = NoteFilter(
        status=status,
        tags=tags.split(",") if tags else None,
        search=search,
        page=page,
        page_size=page_size
    )
    
    notes, total = await note_service.list_notes(db, filters)
    
    return NoteListResponse(
        items=[note.to_dict() for note in notes],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a note by ID"""
    note = await note_service.get_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    update_data: NoteUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a note"""
    note = await note_service.update_note(db, note_id, update_data)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a note"""
    deleted = await note_service.delete_note(db, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}
