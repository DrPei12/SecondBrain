"""
SQLAlchemy model for Notes (Notion-lite structure)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class NoteStatus(str, enum.Enum):
    """Note status workflow"""
    INBOX = "Inbox"
    REVIEWED = "Reviewed"
    ARCHIVED = "Archived"


class Note(Base):
    """
    Note model for the Second Brain platform.
    
    Supports Markdown rendering with the following fields:
    - id: UUID primary key
    - title: Note title
    - content: Markdown formatted body
    - summary: AI-generated summary (reserved field)
    - tags: List of tags (stored as JSON)
    - source_url: Source link
    - created_at: Timestamp
    - status: Workflow status (Inbox/Reviewed/Archived)
    """
    __tablename__ = "notes"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Core content fields
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=True)  # Markdown formatted body
    summary = Column(Text, nullable=True)  # AI-generated summary (reserved)
    
    # Metadata fields
    tags = Column(JSON, default=list)  # List of tags
    source_url = Column(String(2048), nullable=True)  # Source link
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Workflow status
    status = Column(
        Enum(NoteStatus, name="note_status", create_constraint=False),
        default=NoteStatus.INBOX,
        nullable=False,
        index=True
    )
    
    # RAG indexing status
    indexed_for_rag = Column(
        String(20), 
        default="pending",  # pending, indexed, failed
        nullable=False
    )
    
    # Relationships
    # notes can be linked to other notes if needed
    
    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title[:50]}...', status={self.status})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "tags": self.tags or [],
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status.value if isinstance(self.status, NoteStatus) else self.status,
            "indexed_for_rag": self.indexed_for_rag,
        }


# Create indexes for common queries
Index("idx_notes_status_created", Note.status, Note.created_at)
Index("idx_notes_tags", Note.tags, postgresql_using="gin")
