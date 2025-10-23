"""
Document management endpoints - upload, list, get, delete.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from api.schemas.responses import (
    DocumentListResponse,
    DocumentInfo,
    UploadResponse,
    DeleteResponse,
    StatsResponse,
    DocumentMetadata
)
from api.services.rag_service import get_rag_service, RAGService
from pathlib import Path
import tempfile
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/documents/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Upload and process a PDF document.

    **Process:**
    1. Validates PDF file
    2. Extracts text using FormattingExtractor
    3. Cleans extracted text
    4. Creates chunks (section-aware)
    5. Generates embeddings
    6. Stores in pgVector database

    **Returns:** Document ID, processing stats, and timing information

    **Note:** Processing happens synchronously. For large PDFs, this may take 2-5 seconds.
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_path = temp_file.name
        content = await file.read()
        temp_file.write(content)

    try:
        # Process the PDF
        result = await rag_service.process_pdf(
            file_path=temp_path,
            original_filename=file.filename,
            relative_path=file.filename
        )

        return UploadResponse(
            document_id=result['document_id'],
            filename=result['filename'],
            page_count=result['page_count'],
            chunk_count=result['chunk_count'],
            status="completed",
            processing_time_ms=result['processing_time_ms']
        )

    except Exception as e:
        logger.error(f"Error processing {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    limit: int = 100,
    offset: int = 0,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    List all uploaded documents.

    **Parameters:**
    - limit: Maximum number of documents to return (default: 100, max: 1000)
    - offset: Number of documents to skip for pagination (default: 0)

    **Returns:** List of documents with metadata, upload dates, and chunk counts
    """
    if limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 1000"
        )

    try:
        result = await rag_service.list_documents(limit=limit, offset=offset)

        # Convert to response model
        documents = [
            DocumentInfo(
                id=doc['id'],
                filename=doc['filename'],
                upload_date=doc['upload_date'],
                page_count=doc['page_count'],
                chunk_count=doc['chunk_count'],
                metadata=DocumentMetadata(**doc.get('metadata', {})) if doc.get('metadata') else None
            )
            for doc in result['documents']
        ]

        return DocumentListResponse(
            documents=documents,
            total=result['total']
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get information about a specific document.

    **Parameters:**
    - document_id: UUID of the document

    **Returns:** Document metadata including filename, page count, chunk count, and upload date
    """
    try:
        doc = await rag_service.get_document(document_id)

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )

        return DocumentInfo(
            id=doc['id'],
            filename=doc['filename'],
            upload_date=doc['upload_date'],
            page_count=doc['page_count'],
            chunk_count=doc['chunk_count'],
            metadata=DocumentMetadata(**doc.get('metadata', {})) if doc.get('metadata') else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Delete a document and all its chunks.

    **Parameters:**
    - document_id: UUID of the document to delete

    **Returns:** Deletion confirmation with number of chunks deleted

    **Warning:** This operation cannot be undone!
    """
    try:
        result = await rag_service.delete_document(document_id)

        return DeleteResponse(
            deleted=result['deleted'],
            document_id=result['document_id'],
            chunks_deleted=result['chunks_deleted']
        )

    except ValueError as e:
        # Document not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(rag_service: RAGService = Depends(get_rag_service)):
    """
    Get database statistics.

    **Returns:** Overall statistics including:
    - Total number of documents
    - Total number of chunks
    - Database size
    - Average chunks per document
    """
    try:
        stats = await rag_service.get_stats()

        return StatsResponse(
            total_documents=stats['total_documents'],
            total_chunks=stats['total_chunks'],
            database_size=stats['database_size'],
            avg_chunks_per_document=round(stats['avg_chunks_per_document'], 2)
        )

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
