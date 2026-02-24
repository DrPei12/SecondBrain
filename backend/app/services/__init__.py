"""
Package init for services
"""
from app.services.note_service import NoteService, note_service
from app.services.rag_service import RAGService, rag_service

__all__ = ["NoteService", "note_service", "RAGService", "rag_service"]
