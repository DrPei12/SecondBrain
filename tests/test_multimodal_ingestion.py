#!/usr/bin/env python3
"""Smoke checks for modality-aware file ingestion."""
from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.config import settings
from app.services.multimodal_ingest import multimodal_ingestion_service


class FakeUpload:
    def __init__(self, filename: str, content: bytes, content_type: str) -> None:
        self.filename = filename
        self._content = content
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._content


async def run() -> None:
    settings.RAG_UPLOAD_DIR = ".tmp/test_multimodal_uploads"
    Path(settings.RAG_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    table_doc = await multimodal_ingestion_service.ingest_upload(
        FakeUpload("metrics.csv", b"name,value\nRAG,95\nBaseline,87\n", "text/csv"),
        title="Metrics table",
    )
    assert "table" in table_doc.modalities
    assert "modality:table" in table_doc.tags
    assert "| name | value |" in table_doc.content

    image_doc = await multimodal_ingestion_service.ingest_upload(
        FakeUpload("diagram.png", b"not-a-real-image", "image/png"),
        title="Architecture diagram",
        caption="A system diagram showing a parser, vector store, and answer generator.",
    )
    assert image_doc.modalities == ["image"]
    assert "User supplied caption" in image_doc.content
    assert "parser, vector store" in image_doc.content


if __name__ == "__main__":
    asyncio.run(run())
