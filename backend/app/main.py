"""
Second Brain FastAPI application.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import require_api_key
from app.db.connection import close_db, init_db
from app.services.rag_service import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("[SecondBrain] Starting API...")

    await init_db()
    print("[SecondBrain] Database initialized")

    try:
        await asyncio.wait_for(rag_service.initialize(), timeout=30.0)
        print("[SecondBrain] RAG Service initialized")
    except asyncio.TimeoutError:
        rag_service.mark_degraded("RAG Service initialization timed out")
        print("[SecondBrain] RAG Service initialization timed out")
    except Exception as exc:
        rag_service.mark_degraded(str(exc))
        print(f"[SecondBrain] RAG Service failed: {exc}")

    yield

    print("[SecondBrain] Shutting down API...")
    await rag_service.close()
    await close_db()
    print("[SecondBrain] API stopped")


app = FastAPI(
    title="Second Brain API",
    description="Personal Knowledge Management Platform with RAG",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.endpoints import health, notes, rag

app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(
    notes.router,
    prefix="/api/notes",
    tags=["Notes"],
    dependencies=[Depends(require_api_key)],
)
app.include_router(
    rag.router,
    prefix="/api/rag",
    tags=["RAG"],
    dependencies=[Depends(require_api_key)],
)


@app.get("/")
async def root():
    return {
        "name": "Second Brain API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
