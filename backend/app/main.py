"""
Second Brain FastAPI Application
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
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
    
    # Initialize RAG service
    await rag_service.initialize()
    print("✅ RAG Service initialized")
    
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
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
from app.api.endpoints import notes, rag, health

app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(notes.router, prefix="/api/notes", tags=["Notes"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])


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
