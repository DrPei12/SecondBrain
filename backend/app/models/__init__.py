"""
Package init for models
"""
from app.models.note import Note, NoteStatus
from app.models.user import User

__all__ = ["Note", "NoteStatus", "User"]
