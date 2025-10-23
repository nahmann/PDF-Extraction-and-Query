"""
Pydantic response models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status", example="healthy")
    database: str = Field(..., description="Database connection status", example="connected")
    embedder: str = Field(..., description="Embedding model status", example="loaded")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DocumentMetadata(BaseModel):
    """Document metadata"""
    source_path: Optional[str] = None
    relative_path: Optional[str] = None
    extraction_method: Optional[str] = None
    cleaning_warnings: Optional[int] = None


class DocumentInfo(BaseModel):
    """Document information response"""
    id: str = Field(..., description="Document UUID")
    filename: str = Field(..., description="Original filename")
    upload_date: datetime = Field(..., description="Upload timestamp")
    page_count: int = Field(..., description="Number of pages")
    chunk_count: int = Field(..., description="Number of chunks")
    metadata: Optional[DocumentMetadata] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "equity-incentive-plan.pdf",
                "upload_date": "2025-10-17T12:00:00",
                "page_count": 25,
                "chunk_count": 42,
                "metadata": {
                    "relative_path": "Legal & Insurance/equity-incentive-plan.pdf",
                    "extraction_method": "FormattingExtractor"
                }
            }
        }


class DocumentListResponse(BaseModel):
    """List of documents response"""
    documents: List[DocumentInfo] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")


class UploadResponse(BaseModel):
    """PDF upload response"""
    document_id: str = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Uploaded filename")
    page_count: int = Field(..., description="Number of pages extracted")
    chunk_count: int = Field(..., description="Number of chunks created")
    status: str = Field(..., description="Processing status", example="completed")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "board-meeting-minutes.pdf",
                "page_count": 4,
                "chunk_count": 11,
                "status": "completed",
                "processing_time_ms": 2345
            }
        }


class SearchResult(BaseModel):
    """Single search result"""
    text: str = Field(..., description="Chunk text content")
    document_name: str = Field(..., description="Source document filename")
    document_id: str = Field(..., description="Source document UUID")
    relative_path: Optional[str] = Field(None, description="Document relative path")
    chunk_index: int = Field(..., description="Chunk index in document")
    similarity: float = Field(..., description="Similarity score (0-1)", ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Chunk metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Stock options vest over four years with a one-year cliff...",
                "document_name": "equity-incentive-plan.pdf",
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "relative_path": "Legal & Insurance/equity-incentive-plan.pdf",
                "chunk_index": 5,
                "similarity": 0.8523,
                "metadata": {
                    "section": "Vesting Schedule",
                    "is_split_chunk": False
                }
            }
        }


class SearchResponse(BaseModel):
    """Search results response"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Number of results returned")
    search_time_ms: int = Field(..., description="Search execution time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the vesting terms?",
                "results": [
                    {
                        "text": "Stock options vest over four years...",
                        "document_name": "equity-incentive-plan.pdf",
                        "similarity": 0.85,
                        "chunk_index": 5
                    }
                ],
                "total_results": 3,
                "search_time_ms": 145
            }
        }


class DeleteResponse(BaseModel):
    """Document deletion response"""
    deleted: bool = Field(..., description="Whether deletion was successful")
    document_id: str = Field(..., description="Deleted document UUID")
    chunks_deleted: int = Field(..., description="Number of chunks deleted")


class StatsResponse(BaseModel):
    """Database statistics response"""
    total_documents: int = Field(..., description="Total number of documents")
    total_chunks: int = Field(..., description="Total number of chunks")
    database_size: str = Field(..., description="Human-readable database size")
    avg_chunks_per_document: float = Field(..., description="Average chunks per document")

    class Config:
        json_schema_extra = {
            "example": {
                "total_documents": 490,
                "total_chunks": 8532,
                "database_size": "125 MB",
                "avg_chunks_per_document": 17.4
            }
        }


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Document not found",
                "detail": "No document with ID 123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2025-10-17T12:00:00"
            }
        }
