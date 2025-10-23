"""
Health check endpoint.
"""

from fastapi import APIRouter, Depends
from api.schemas.responses import HealthResponse
from api.services.rag_service import get_rag_service, RAGService
from datetime import datetime

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(rag_service: RAGService = Depends(get_rag_service)):
    """
    Check API health status.

    Returns system health including database and embedder status.
    """
    health_status = rag_service.health_check()

    return HealthResponse(
        status=health_status['status'],
        database=health_status['database'],
        embedder=health_status['embedder'],
        timestamp=datetime.utcnow()
    )
