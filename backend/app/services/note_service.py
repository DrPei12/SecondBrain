"""
Note service for CRUD operations
"""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.note import Note, NoteStatus
from app.schemas.note import NoteCreate, NoteUpdate, NoteFilter


class NoteService:
    """Service class for note CRUD operations"""
    
    async def create_note(
        self, 
        db: AsyncSession, 
        note_data: NoteCreate
    ) -> Note:
        """Create a new note"""
        note = Note(
            id=str(uuid.uuid4()),
            title=note_data.title,
            content=note_data.content,
            tags=note_data.tags,
            source_url=note_data.source_url,
            status=NoteStatus.INBOX,
            indexed_for_rag="pending"
        )
        
        db.add(note)
        await db.commit()
        await db.refresh(note)
        
        return note
    
    async def create_notes_batch(
        self, 
        db: AsyncSession, 
        notes_data: List[NoteCreate]
    ) -> Tuple[List[Note], List[dict]]:
        """Create multiple notes in batch"""
        created = []
        failed = []
        
        for idx, note_data in enumerate(notes_data):
            try:
                note = await self.create_note(db, note_data)
                created.append(note)
            except Exception as e:
                failed.append({
                    "index": idx,
                    "error": str(e),
                    "data": note_data.model_dump() if hasattr(note_data, 'model_dump') else dict(note_data)
                })
        
        return created, failed
    
    async def get_note_by_id(
        self, 
        db: AsyncSession, 
        note_id: str
    ) -> Optional[Note]:
        """Get a note by ID"""
        result = await db.execute(
            select(Note).where(Note.id == note_id)
        )
        return result.scalar_one_or_none()
    
    async def list_notes(
        self, 
        db: AsyncSession, 
        filters: Optional[NoteFilter] = None
    ) -> Tuple[List[Note], int]:
        """List notes with optional filters"""
        if filters is None:
            filters = NoteFilter()
        
        query = select(Note)
        
        # Apply filters
        if filters.status:
            query = query.where(Note.status == NoteStatus(filters.status))
        
        if filters.tags:
            for tag in filters.tags:
                query = query.where(Note.tags.contains([tag]))
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                (Note.title.ilike(search_term)) | 
                (Note.content.ilike(search_term))
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        query = query.order_by(Note.created_at.desc())
        query = query.offset(offset).limit(filters.page_size)
        
        result = await db.execute(query)
        notes = result.scalars().all()
        
        return list(notes), total
    
    async def update_note(
        self, 
        db: AsyncSession, 
        note_id: str, 
        update_data: NoteUpdate
    ) -> Optional[Note]:
        """Update a note"""
        note = await self.get_note_by_id(db, note_id)
        if not note:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            setattr(note, field, value)
        
        if "content" in update_dict or "title" in update_dict:
            note.indexed_for_rag = "pending"
        
        await db.commit()
        await db.refresh(note)
        
        return note
    
    async def delete_note(
        self, 
        db: AsyncSession, 
        note_id: str
    ) -> bool:
        """Delete a note"""
        note = await self.get_note_by_id(db, note_id)
        if not note:
            return False
        
        await db.delete(note)
        await db.commit()
        
        return True
    
    async def get_notes_for_rag_indexing(
        self, 
        db: AsyncSession, 
        note_ids: Optional[List[str]] = None,
        force: bool = False
    ) -> List[Note]:
        """Get notes pending RAG indexing"""
        query = select(Note)
        
        if note_ids:
            query = query.where(Note.id.in_(note_ids))
        else:
            if force:
                query = query.where(Note.indexed_for_rag.in_(["pending", "failed"]))
            else:
                query = query.where(Note.indexed_for_rag == "pending")
        
        query = query.order_by(Note.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())


# Singleton instance
note_service = NoteService()
