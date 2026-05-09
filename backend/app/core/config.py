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
    RAG_ENGINE: str = os.getenv("RAG_ENGINE", "vector")
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "1600"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
    RAG_VECTOR_STORE_FILE: str = os.getenv(
        "RAG_VECTOR_STORE_FILE",
        "./rag_data/vector_store.json"
    )

    # Model provider. Values: openai, bailian.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_BASE_URL: str = os.getenv(
        "OPENAI_BASE_URL",
        os.getenv("OPENAI_API_BASE", "")
    )
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

    # Bailian / DashScope OpenAI-compatible settings.
    DASHSCOPE_API_KEY: str = os.getenv(
        "DASHSCOPE_API_KEY",
        os.getenv("BAILIAN_API_KEY", "")
    )
    BAILIAN_BASE_URL: str = os.getenv(
        "BAILIAN_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    BAILIAN_LLM_MODEL: str = os.getenv("BAILIAN_LLM_MODEL", "qwen3.6-plus")
    BAILIAN_EMBEDDING_MODEL: str = os.getenv(
        "BAILIAN_EMBEDDING_MODEL",
        "text-embedding-v4"
    )
    BAILIAN_EMBEDDING_DIMENSIONS: int = int(
        os.getenv("BAILIAN_EMBEDDING_DIMENSIONS", "1024")
    )
    BAILIAN_ENABLE_THINKING: bool = (
        os.getenv("BAILIAN_ENABLE_THINKING", "false").lower() == "true"
    )
    
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
