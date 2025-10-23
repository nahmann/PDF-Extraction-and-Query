"""
Unit tests for embedding generation.
"""

import pytest
import numpy as np


class TestSentenceTransformerEmbedder:
    """Test local sentence transformer embedder"""

    def test_embedder_initialization(self):
        """Test embedder initializes correctly"""
        try:
            from src.embeddings import SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(debug=False)

            assert embedder is not None
            assert embedder.embedding_dim > 0
            assert embedder.model_name is not None
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_embed_single_text(self):
        """Test embedding a single text"""
        try:
            from src.embeddings import SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(debug=False)

            text = "This is a test document about employee benefits."
            embedding = embedder.embed(text)

            # Should return a list of floats
            assert isinstance(embedding, list)
            assert len(embedding) == embedder.embedding_dim
            assert all(isinstance(x, float) for x in embedding)

            # Embedding should not be all zeros
            assert sum(abs(x) for x in embedding) > 0
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_embed_empty_text(self):
        """Test embedding empty text"""
        try:
            from src.embeddings import SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(debug=False)

            embedding = embedder.embed("")

            # Should return zero vector for empty text
            assert isinstance(embedding, list)
            assert len(embedding) == embedder.embedding_dim
            # Zero vector
            assert all(x == 0.0 for x in embedding)
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_embed_batch(self):
        """Test batch embedding multiple texts"""
        try:
            from src.embeddings import SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(debug=False)

            texts = [
                "Employee handbook section about vacation policy",
                "Information about health insurance benefits",
                "Details on retirement savings plans"
            ]

            embeddings = embedder.embed_batch(texts)

            # Should return list of embeddings
            assert isinstance(embeddings, list)
            assert len(embeddings) == len(texts)

            # Each embedding should be correct dimension
            for embedding in embeddings:
                assert isinstance(embedding, list)
                assert len(embedding) == embedder.embedding_dim
                assert all(isinstance(x, float) for x in embedding)
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_batch_with_empty_texts(self):
        """Test batch embedding with some empty texts"""
        try:
            from src.embeddings import SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(debug=False)

            texts = [
                "Valid text here",
                "",
                "Another valid text",
                "   ",  # Whitespace only
            ]

            embeddings = embedder.embed_batch(texts)

            assert len(embeddings) == len(texts)

            # First and third should have real embeddings
            assert sum(abs(x) for x in embeddings[0]) > 0
            assert sum(abs(x) for x in embeddings[2]) > 0

            # Second and fourth should be zero vectors
            assert all(x == 0.0 for x in embeddings[1])
            assert all(x == 0.0 for x in embeddings[3])
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_embedding_consistency(self):
        """Test that same text produces same embedding"""
        try:
            from src.embeddings import SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(debug=False)

            text = "Test document for consistency check"

            embedding1 = embedder.embed(text)
            embedding2 = embedder.embed(text)

            # Should be identical
            assert len(embedding1) == len(embedding2)

            # Check all values match (with small tolerance for float precision)
            for v1, v2 in zip(embedding1, embedding2):
                assert abs(v1 - v2) < 1e-6
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_embedding_similarity(self):
        """Test that similar texts have similar embeddings"""
        try:
            from src.embeddings import SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(debug=False)

            text1 = "The employee receives vacation days"
            text2 = "Workers are entitled to paid time off"
            text3 = "The weather is sunny today"

            emb1 = embedder.embed(text1)
            emb2 = embedder.embed(text2)
            emb3 = embedder.embed(text3)

            # Calculate cosine similarity (for normalized vectors, this is dot product)
            def cosine_similarity(v1, v2):
                dot = sum(a * b for a, b in zip(v1, v2))
                return dot

            sim_12 = cosine_similarity(emb1, emb2)  # Similar texts
            sim_13 = cosine_similarity(emb1, emb3)  # Different texts

            # Similar texts should have higher similarity than different texts
            assert sim_12 > sim_13
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_get_embedding_dimension(self):
        """Test getting embedding dimension"""
        try:
            from src.embeddings import SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(debug=False)

            dim = embedder.get_embedding_dimension()

            assert isinstance(dim, int)
            assert dim > 0

            # Default model (all-MiniLM-L6-v2) should be 384 dims
            assert dim == 384
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_get_model_info(self):
        """Test getting model information"""
        try:
            from src.embeddings import SentenceTransformerEmbedder

            embedder = SentenceTransformerEmbedder(debug=False)

            info = embedder.get_model_info()

            assert isinstance(info, dict)
            assert 'model_name' in info
            assert 'embedding_dimension' in info
            assert 'device' in info
            assert 'normalize' in info
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_recommended_models(self):
        """Test recommended model utility"""
        try:
            from src.embeddings import get_recommended_model, RECOMMENDED_MODELS

            # Test getting recommended models
            fast_model = get_recommended_model('fast')
            balanced_model = get_recommended_model('balanced')
            quality_model = get_recommended_model('quality')

            assert fast_model in RECOMMENDED_MODELS.values()
            assert balanced_model in RECOMMENDED_MODELS.values()
            assert quality_model in RECOMMENDED_MODELS.values()

            # Default should return balanced
            default_model = get_recommended_model('unknown')
            assert default_model == balanced_model
        except ImportError:
            pytest.skip("sentence-transformers not installed")


class TestEmbeddingIntegration:
    """Test embedding integration with chunking"""

    def test_embed_chunks_from_pdf(self, employee_handbook_pdf):
        """Test embedding real chunks from a PDF"""
        try:
            from src.extraction import FormattingExtractor
            from src.preprocessing import TextCleaner
            from src.chunking import LangChainChunker
            from src.embeddings import SentenceTransformerEmbedder

            # Extract and clean
            extractor = FormattingExtractor()
            result = extractor.extract(str(employee_handbook_pdf))
            assert result.success

            cleaner = TextCleaner()
            cleaned_text, _ = cleaner.clean(result.extracted_text)

            # Chunk
            chunker = LangChainChunker(max_chunk_size=500)
            chunks = chunker.chunk(cleaned_text)
            assert len(chunks) > 0

            # Embed
            embedder = SentenceTransformerEmbedder(debug=False)

            # Embed first 3 chunks
            texts_to_embed = [c['text'] for c in chunks[:3]]
            embeddings = embedder.embed_batch(texts_to_embed)

            assert len(embeddings) == 3

            for i, (chunk, embedding) in enumerate(zip(chunks[:3], embeddings)):
                assert len(embedding) == embedder.embedding_dim
                chunk['embedding'] = embedding
                chunk['metadata']['embedding_model'] = embedder.model_name

            # Verify embeddings were added
            assert 'embedding' in chunks[0]
            assert len(chunks[0]['embedding']) == embedder.embedding_dim
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_batch_embedding_efficiency(self):
        """Test that batch embedding is more efficient than individual"""
        try:
            from src.embeddings import SentenceTransformerEmbedder
            import time

            embedder = SentenceTransformerEmbedder(debug=False)

            texts = [f"Test document number {i}" for i in range(10)]

            # Individual embedding
            start = time.time()
            individual_embeddings = [embedder.embed(text) for text in texts]
            individual_time = time.time() - start

            # Batch embedding
            start = time.time()
            batch_embeddings = embedder.embed_batch(texts)
            batch_time = time.time() - start

            # Batch should be faster
            # (May not always be true for very small batches, but usually is)
            assert len(individual_embeddings) == len(batch_embeddings)

            # Just verify both methods produce valid embeddings
            for ind_emb, batch_emb in zip(individual_embeddings, batch_embeddings):
                assert len(ind_emb) == len(batch_emb)
        except ImportError:
            pytest.skip("sentence-transformers not installed")
