"""
Base vector store interface.

Part 4: Vector Database Integration
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseVectorStore(ABC):
    """Abstract base class for vector stores"""

    @abstractmethod
    def insert(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]:
        """Insert vectors with metadata"""
        pass

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> int:
        """Delete vectors by ID"""
        pass
