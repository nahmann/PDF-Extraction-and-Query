"""
Pydantic request models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class SearchRequest(BaseModel):
    """Request model for document search"""
    query: str = Field(
        ...,
        description="Natural language search query",
        min_length=1,
        max_length=1000,
        example="What are the stock option vesting terms?"
    )
    top_k: int = Field(
        default=3,
        description="Number of results to return",
        ge=1,
        le=20,
        example=3
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Optional: Filter results to specific document UUID",
        example="123e4567-e89b-12d3-a456-426614174000"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the vesting terms for stock options?",
                "top_k": 3
            }
        }
