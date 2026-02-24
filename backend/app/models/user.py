"""
SQLAlchemy model for User
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.db.base import Base


class User(Base):
    """
    User model for authentication and ownership
    """
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(String(10), default="active", nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
