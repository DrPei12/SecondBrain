"""
OpenAI-compatible model provider abstraction.

The implementation intentionally keeps vendor-specific details at the edge so
RAG code can use the same chat and embedding methods for OpenAI, Bailian, or
another compatible provider.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Sequence

from openai import OpenAI

from app.core.config import settings


@dataclass(frozen=True)
class ProviderStatus:
    provider: str
    configured: bool
    base_url: str
    llm_model: str
    embedding_model: str
    embedding_dimensions: int
    thinking_enabled: bool | None = None


class OpenAICompatibleProvider:
    """Small async wrapper around the synchronous OpenAI Python SDK."""

    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER.strip().lower() or "openai"

        if self.provider == "bailian":
            self.api_key = settings.DASHSCOPE_API_KEY.strip()
            self.base_url = settings.BAILIAN_BASE_URL.strip()
            self.llm_model = settings.BAILIAN_LLM_MODEL.strip()
            self.embedding_model = settings.BAILIAN_EMBEDDING_MODEL.strip()
            self.embedding_dimensions = settings.BAILIAN_EMBEDDING_DIMENSIONS
            self.thinking_enabled = settings.BAILIAN_ENABLE_THINKING
        else:
            self.provider = "openai"
            self.api_key = settings.OPENAI_API_KEY.strip()
            self.base_url = settings.OPENAI_BASE_URL.strip()
            self.llm_model = settings.LLM_MODEL.strip()
            self.embedding_model = settings.EMBEDDING_MODEL.strip()
            self.embedding_dimensions = settings.EMBEDDING_DIMENSIONS
            self.thinking_enabled = None

        self._client: OpenAI | None = None
        if self.api_key:
            kwargs: dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)

    @property
    def configured(self) -> bool:
        return bool(self._client and self.api_key and self.llm_model and self.embedding_model)

    @property
    def status(self) -> ProviderStatus:
        return ProviderStatus(
            provider=self.provider,
            configured=self.configured,
            base_url=self.base_url,
            llm_model=self.llm_model,
            embedding_model=self.embedding_model,
            embedding_dimensions=self.embedding_dimensions,
            thinking_enabled=self.thinking_enabled,
        )

    def ensure_configured(self) -> None:
        if not self.configured:
            if self.provider == "bailian":
                raise RuntimeError("DASHSCOPE_API_KEY is not configured")
            raise RuntimeError("OPENAI_API_KEY is not configured")

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Return embeddings for a non-empty list of texts."""
        self.ensure_configured()
        clean_texts = [text if text else " " for text in texts]
        if not clean_texts:
            return []
        return await asyncio.to_thread(self._embed_texts_sync, clean_texts)

    def _embed_texts_sync(self, texts: list[str]) -> list[list[float]]:
        assert self._client is not None
        params: dict[str, Any] = {
            "model": self.embedding_model,
            "input": texts,
            "encoding_format": "float",
        }
        if self.embedding_dimensions > 0:
            params["dimensions"] = self.embedding_dimensions

        response = self._client.embeddings.create(**params)
        return [list(item.embedding) for item in response.data]

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
    ) -> str:
        """Return a plain assistant response for chat-completions models."""
        self.ensure_configured()
        return await asyncio.to_thread(
            self._chat_sync,
            messages,
            temperature,
        )

    def _chat_sync(self, messages: list[dict[str, str]], temperature: float) -> str:
        assert self._client is not None
        params: dict[str, Any] = {
            "model": self.llm_model,
            "messages": messages,
            "temperature": temperature,
        }
        if self.provider == "bailian":
            params["extra_body"] = {"enable_thinking": self.thinking_enabled}

        response = self._client.chat.completions.create(**params)
        content = response.choices[0].message.content or ""
        return content.strip()
