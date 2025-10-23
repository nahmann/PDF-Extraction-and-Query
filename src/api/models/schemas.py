"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    job_id: str
    filename: str
    status: str


class SearchRequest(BaseModel):
    """Request for document search"""
    query: str = Field(..., description="Search query")
    top_k: int = Field(10, ge=1, le=100, description="Number of results")
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Single search result"""
    chunk_id: str
    document_id: str
    document_name: str
    text: str
    score: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Response for search request"""
    query: str
    results: List[SearchResult]
    total_results: int
