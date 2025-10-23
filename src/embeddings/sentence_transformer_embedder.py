"""
Local embedding generation using Sentence Transformers.

Provides free, offline embeddings without API calls.
Uses HuggingFace models that run locally.
"""

from typing import List, Optional
import numpy as np

from embeddings.base_embedder import BaseEmbedder
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning(
        "sentence-transformers not installed. "
        "Install with: pip install sentence-transformers"
    )


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Generate embeddings using Sentence Transformers models.

    Completely local - no API calls, no costs, works offline.

    Recommended models:
    - 'all-MiniLM-L6-v2': Fast, lightweight (384 dims, ~80MB)
    - 'all-mpnet-base-v2': Better quality (768 dims, ~420MB)
    - 'BAAI/bge-large-en-v1.5': SOTA quality (1024 dims, ~1.3GB)
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        normalize: bool = True,
        debug: bool = False
    ):
        """
        Initialize the sentence transformer embedder.

        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
            device: Device to use ('cuda', 'cpu', or None for auto)
            normalize: Whether to normalize embeddings to unit length
            debug: Enable debug logging
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for local embeddings. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.device = device
        self.normalize = normalize
        self.debug = debug
        self.logger = logger

        # Load model (will download on first use)
        if self.debug:
            self.logger.info(f"Loading embedding model: {model_name}")

        try:
            self.model = SentenceTransformer(model_name, device=device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()

            if self.debug:
                self.logger.info(
                    f"Model loaded successfully. "
                    f"Embedding dimension: {self.embedding_dim}"
                )
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.embedding_dim

        try:
            embedding = self.model.encode(
                text,
                normalize_embeddings=self.normalize,
                show_progress_bar=False
            )

            # Convert numpy array to list
            return embedding.tolist()

        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts but remember their positions
        non_empty_texts = []
        non_empty_indices = []

        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text)
                non_empty_indices.append(i)

        if not non_empty_texts:
            # All texts were empty
            return [[0.0] * self.embedding_dim] * len(texts)

        try:
            # Batch encode is much faster than individual encodes
            embeddings = self.model.encode(
                non_empty_texts,
                normalize_embeddings=self.normalize,
                show_progress_bar=self.debug,
                batch_size=32
            )

            # Convert to list and insert zero vectors for empty texts
            result = []
            zero_vector = [0.0] * self.embedding_dim
            non_empty_idx = 0

            for i in range(len(texts)):
                if i in non_empty_indices:
                    result.append(embeddings[non_empty_idx].tolist())
                    non_empty_idx += 1
                else:
                    result.append(zero_vector)

            return result

        except Exception as e:
            self.logger.error(f"Error generating batch embeddings: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.

        Returns:
            Embedding dimension (e.g., 384, 768, 1024)
        """
        return self.embedding_dim

    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "device": str(self.model.device),
            "normalize": self.normalize,
            "max_seq_length": self.model.max_seq_length
        }


# Model recommendations by use case
RECOMMENDED_MODELS = {
    "fast": "sentence-transformers/all-MiniLM-L6-v2",  # 384 dims, ~80MB
    "balanced": "sentence-transformers/all-mpnet-base-v2",  # 768 dims, ~420MB
    "quality": "BAAI/bge-large-en-v1.5",  # 1024 dims, ~1.3GB
    "multilingual": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  # 768 dims
}


def get_recommended_model(use_case: str = "balanced") -> str:
    """
    Get recommended model name for a use case.

    Args:
        use_case: One of 'fast', 'balanced', 'quality', 'multilingual'

    Returns:
        Model name string
    """
    return RECOMMENDED_MODELS.get(use_case, RECOMMENDED_MODELS["balanced"])
