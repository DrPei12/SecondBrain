"""
Health check endpoints
"""
from fastapi import APIRouter

from app.services.rag_service import rag_service

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check():
    """Readiness check (includes dependencies)"""
    rag_stats = await rag_service.get_index_stats()
    ready = bool(rag_stats.get("ready"))
    return {
        "status": "ready" if ready else "degraded",
        "database": "connected",
        "rag": {
            "ready": ready,
            "engine": rag_stats.get("engine"),
            "provider": rag_stats.get("provider", {}),
            "degraded_reason": rag_stats.get("degraded_reason"),
            "vector_store": rag_stats.get("vector_store", {}),
        },
    }
