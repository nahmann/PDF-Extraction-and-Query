"""
Search endpoints for document querying.
"""

from fastapi import APIRouter, Depends, HTTPException
from api.schemas.requests import SearchRequest
from api.schemas.responses import SearchResponse, SearchResult
from api.services.rag_service import get_rag_service, RAGService

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Search documents using semantic similarity.

    Performs vector similarity search across all uploaded documents.
    Returns the top-k most relevant chunks with similarity scores.

    **Example queries:**
    - "What are the stock option vesting terms?"
    - "Who are the board members?"
    - "What is the company's cybersecurity policy?"
    - "What were the Series C funding terms?"

    **Similarity scores:**
    - 0.8-1.0: Highly relevant
    - 0.6-0.8: Moderately relevant
    - 0.4-0.6: Weakly relevant
    - < 0.4: Likely not relevant
    """
    try:
        result = await rag_service.search_documents(
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id
        )

        return SearchResponse(
            query=result['query'],
            results=[SearchResult(**r) for r in result['results']],
            total_results=result['total_results'],
            search_time_ms=result['search_time_ms']
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
