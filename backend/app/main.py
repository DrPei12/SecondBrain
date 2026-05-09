"""
Second Brain FastAPI Application
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.security import require_api_key
from app.db.connection import init_db, close_db
from app.services.rag_service import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("🚀 Starting Second Brain...")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Initialize RAG service (skip if hanging)
    try:
        await asyncio.wait_for(rag_service.initialize(), timeout=30.0)
        print("✅ RAG Service initialized")
    except asyncio.TimeoutError:
        rag_service.mark_degraded("RAG Service initialization timed out")
        print("⚠️ RAG Service initialization timed out, running in degraded mode")
    except Exception as e:
        rag_service.mark_degraded(str(e))
        print(f"⚠️ RAG Service failed: {e}, running in degraded mode")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down Second Brain...")
    await rag_service.close()
    await close_db()
    print("👋 Second Brain stopped")


# Create FastAPI app
app = FastAPI(
    title="Second Brain API",
    description="Personal Knowledge Management Platform with RAG",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
from app.api.endpoints import notes, rag, health

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


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Second Brain API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
