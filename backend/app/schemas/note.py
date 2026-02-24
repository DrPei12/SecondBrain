"""
Pydantic schemas for Note API
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class NoteStatusEnum(str, Enum):
    """Note status enum for validation"""
    INBOX = "Inbox"
    REVIEWED = "Reviewed"
    ARCHIVED = "Archived"


# ================== Note Schemas ==================

class NoteBase(BaseModel):
    """Base note schema with common fields"""
    title: str = Field(..., min_length=1, max_length=500, description="Note title")
    content: Optional[str] = Field(None, description="Markdown formatted content")
    tags: Optional[List[str]] = Field(default_factory=list, description="List of tags")
    source_url: Optional[str] = Field(None, max_length=2048, description="Source URL")


class NoteCreate(NoteBase):
    """Schema for creating a note"""
    status: Optional[NoteStatusEnum] = Field(
        default=NoteStatusEnum.INBOX,
        description="Initial status (default: Inbox)"
    )


class NoteUpdate(BaseModel):
    """Schema for updating a note"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    source_url: Optional[str] = None
    status: Optional[NoteStatusEnum] = None


class NoteResponse(NoteBase):
    """Schema for note response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    summary: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str
    indexed_for_rag: str = "pending"


class NoteListResponse(BaseModel):
    """Schema for list of notes response"""
    items: List[NoteResponse]
    total: int
    page: int
    page_size: int


# ================== Batch Note Schemas ==================

class BatchNoteCreate(BaseModel):
    """Schema for batch note creation"""
    notes: List[NoteCreate]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "notes": [
                    {
                        "title": "Note Title 1",
                        "content": "Markdown content...",
                        "tags": ["tag1", "tag2"],
                        "source_url": "https://example.com"
                    },
                    {
                        "title": "Note Title 2",
                        "content": "Another note...",
                        "tags": ["tag3"]
                    }
                ]
            }
        }
    }


class BatchNoteResponse(BaseModel):
    """Schema for batch creation response"""
    created: List[NoteResponse]
    failed: List[dict]  # Items that failed with error info
    total_created: int
    total_failed: int


# ================== Query/Filter Schemas ==================

class NoteFilter(BaseModel):
    """Schema for filtering notes"""
    status: Optional[NoteStatusEnum] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = Field(None, description="Search in title and content")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
