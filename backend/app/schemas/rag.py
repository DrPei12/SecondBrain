"""
Pydantic schemas for RAG API
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    """Schema for RAG query request"""
    query: str = Field(..., min_length=1, description="Natural language query")
    mode: str = Field(
        default="mix",
        description="Query mode: local, global, hybrid, naive, mix, bypass"
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "What are the key insights about AI from my notes?",
                "mode": "mix",
                "top_k": 10
            }
        }
    }


class RAGQueryResponse(BaseModel):
    """Schema for RAG query response"""
    query: str
    answer: str
    sources: List[dict] = Field(default_factory=list, description="Source notes used")
    mode: str


class RAGIndexRequest(BaseModel):
    """Schema for RAG indexing request"""
    note_ids: Optional[List[str]] = Field(
        None, 
        description="Specific note IDs to index. If None, index all pending notes."
    )
    force_reindex: bool = Field(
        default=False,
        description="Force reindexing of already indexed notes"
    )


class RAGIndexResponse(BaseModel):
    """Schema for RAG indexing response"""
    indexed_count: int
    failed_count: int
    status: str
    message: str
