"""
Chunker factory for creating chunker instances based on configuration.

RECOMMENDED: Use "langchain" (section-aware) for best similarity scores.
Based on evaluation with 490 M&A documents:
- "langchain" (section-aware): 0.580 similarity - BEST
- "langchain_simple" (size-based): 0.516 similarity - 11% worse

See evaluation/CHUNKING_COMPARISON_RESULTS.md for details.
"""

from typing import Optional

from chunking.base_chunker import BaseChunker
from chunking.langchain_chunker import LangChainChunker
from config.settings import settings


def create_chunker(
    chunker_type: Optional[str] = None,
    max_chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    debug: bool = False
) -> BaseChunker:
    """
    Create a chunker instance based on type.

    RECOMMENDED: Use "langchain" (section-aware) for best similarity scores.

    Args:
        chunker_type: Type of chunker
                     - "langchain" (RECOMMENDED): Section-aware, best similarity (0.580)
                     - "langchain_simple": Size-based, splits at paragraphs/sentences (0.516)
                     If None, uses settings.chunker_type
        max_chunk_size: Maximum chunk size (if None, uses settings.max_chunk_size)
        chunk_overlap: Chunk overlap (if None, uses settings.chunk_overlap)
        debug: Enable debug logging

    Returns:
        Configured chunker instance

    Raises:
        ValueError: If chunker_type is invalid
    """
    chunk_type = chunker_type or settings.chunker_type
    chunk_size = max_chunk_size or settings.max_chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    # RECOMMENDED: Section-aware (best similarity scores)
    if chunk_type == "langchain":
        return LangChainChunker(
            max_chunk_size=chunk_size,
            chunk_overlap=overlap,
            use_section_awareness=True,  # Preserves document structure - BEST
            debug=debug
        )

    # Size-based mode (alternative, 11% worse similarity)
    elif chunk_type == "langchain_simple":
        return LangChainChunker(
            max_chunk_size=chunk_size,
            chunk_overlap=overlap,
            use_section_awareness=False,  # Size-based with smart boundaries
            debug=debug
        )

    else:
        raise ValueError(
            f"Invalid chunker_type: '{chunk_type}'. "
            f"Must be 'langchain' (recommended) or 'langchain_simple'"
        )


def get_chunker_info(chunker: BaseChunker) -> dict:
    """
    Get information about a chunker instance.

    Args:
        chunker: Chunker instance

    Returns:
        Dict with chunker info
    """
    return {
        "type": chunker.__class__.__name__,
        "max_chunk_size": chunker.max_chunk_size,
        "chunk_overlap": chunker.chunk_overlap,
    }
