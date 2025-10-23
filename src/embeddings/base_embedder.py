"""
Base embedder class for generating vector embeddings.

Part 3: Embedding Generation Service
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseEmbedder(ABC):
    """Abstract base class for embedding generators"""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass
