"""
Core configuration for Second Brain application
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Second Brain"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./second_brain.db"
    )
    
    # RAG Configuration
    RAG_WORKING_DIR: str = os.getenv("RAG_WORKING_DIR", "./rag_data")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SECOND_BRAIN_API_KEY: str = os.getenv("SECOND_BRAIN_API_KEY", "")
    BACKEND_CORS_ORIGINS: str = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:3003,http://127.0.0.1:3003"
    )
    
    # Server
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    @property
    def cors_origins(self) -> list[str]:
        """Return configured CORS origins as a normalized list."""
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
