"""
Base chunker class for text chunking strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseChunker(ABC):
    """Abstract base class for text chunkers"""

    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach

        Returns:
            List of chunk dictionaries
        """
        pass
