"""
Embedding generation module (Part 3).
"""

from embeddings.base_embedder import BaseEmbedder
from embeddings.bedrock_embedder import BedrockEmbedder
from embeddings.sentence_transformer_embedder import (
    SentenceTransformerEmbedder,
    get_recommended_model,
    RECOMMENDED_MODELS
)

__all__ = [
    'BaseEmbedder',
    'BedrockEmbedder',
    'SentenceTransformerEmbedder',
    'get_recommended_model',
    'RECOMMENDED_MODELS'
]
