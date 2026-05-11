"""
Core configuration for Second Brain application
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


def _read_secret_file(path: str) -> str:
    """Read a local secret file without logging or normalizing the value."""
    if not path:
        return ""
    with open(path, "r", encoding="utf-8-sig") as secret_file:
        return secret_file.read().strip()


def _secret_from_env(value_names: tuple[str, ...], file_names: tuple[str, ...]) -> str:
    for name in value_names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    for name in file_names:
        path = os.getenv(name, "").strip()
        if path:
            return _read_secret_file(path)
    return ""


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
    RAG_INDEX_RETRIES: int = int(os.getenv("RAG_INDEX_RETRIES", "1"))
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
    DASHSCOPE_API_KEY_FILE: str = os.getenv("DASHSCOPE_API_KEY_FILE", "")
    BAILIAN_API_KEY_FILE: str = os.getenv("BAILIAN_API_KEY_FILE", "")
    DASHSCOPE_API_KEY: str = _secret_from_env(
        ("DASHSCOPE_API_KEY", "BAILIAN_API_KEY"),
        ("DASHSCOPE_API_KEY_FILE", "BAILIAN_API_KEY_FILE"),
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
    SECOND_BRAIN_API_KEY_FILE: str = os.getenv("SECOND_BRAIN_API_KEY_FILE", "")
    SECOND_BRAIN_API_KEY: str = _secret_from_env(
        ("SECOND_BRAIN_API_KEY",),
        ("SECOND_BRAIN_API_KEY_FILE",),
    )
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
