"""
Tests for PostgreSQL + pgvector vector store.

NOTE: These tests require a running PostgreSQL instance with pgvector extension.
Set up test database with:
    createdb pdf_rag_test
    psql pdf_rag_test -c "CREATE EXTENSION vector;"

Set DATABASE_URL environment variable for tests:
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/pdf_rag_test"
"""

import pytest
import os
from typing import List
import uuid

from src.vector_store.pgvector_client import PgVectorStore
from src.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder


# Skip all tests if database is not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or "user:password" in os.getenv("DATABASE_URL", ""),
    reason="Database not configured. Set DATABASE_URL environment variable."
)


@pytest.fixture(scope="module")
def embedder():
    """Create embedder for generating test embeddings"""
    return SentenceTransformerEmbedder(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        device="cpu"
    )


@pytest.fixture(scope="module")
def vector_store():
    """Create and initialize vector store for tests"""
    store = PgVectorStore(
        connection_string=os.getenv("DATABASE_URL"),
        embedding_dim=384,
        debug=True
    )

    # Initialize database (safe to run multiple times)
    store.initialize_database()

    yield store

    # Cleanup
    store.close()


@pytest.fixture
def sample_document(vector_store):
    """Create a sample document for testing"""
    doc_id = vector_store.insert_document(
        filename="test_document.pdf",
        page_count=5,
        metadata={"test": True, "category": "sample"}
    )

    yield doc_id

    # Cleanup: delete document after test
    vector_store.delete_document(doc_id)


@pytest.fixture
def sample_chunks(vector_store, sample_document, embedder):
    """Create sample chunks with embeddings"""
    texts = [
        "This is the first chunk about employee policies.",
        "The second chunk discusses vacation benefits.",
        "Health insurance information is in this chunk.",
        "Remote work guidelines are described here.",
        "Final chunk covers performance reviews."
    ]

    embeddings = embedder.embed_batch(texts)

    chunks = [
        {
            "text": text,
            "embedding": embedding,
            "metadata": {"page": i + 1, "test": True}
        }
        for i, (text, embedding) in enumerate(zip(texts, embeddings))
    ]

    chunk_ids = vector_store.insert_chunks(sample_document, chunks)

    yield chunk_ids

    # Cleanup handled by document deletion


class TestDatabaseInitialization:
    """Test database setup and initialization"""

    def test_initialize_database(self, vector_store):
        """Test database initialization is idempotent"""
        # Should not raise error when called multiple times
        result = vector_store.initialize_database()
        assert result is True

    def test_get_initial_stats(self, vector_store):
        """Test getting database statistics"""
        stats = vector_store.get_stats()

        assert "document_count" in stats
        assert "chunk_count" in stats
        assert "embedding_dimension" in stats
        assert stats["embedding_dimension"] == 384
        assert isinstance(stats["document_count"], int)
        assert isinstance(stats["chunk_count"], int)


class TestDocumentOperations:
    """Test document CRUD operations"""

    def test_insert_document(self, vector_store):
        """Test inserting a document"""
        doc_id = vector_store.insert_document(
            filename="test.pdf",
            page_count=10,
            metadata={"author": "Test Author"}
        )

        assert doc_id is not None
        assert len(doc_id) == 36  # UUID format

        # Cleanup
        vector_store.delete_document(doc_id)

    def test_get_document(self, vector_store, sample_document):
        """Test retrieving a document by ID"""
        doc = vector_store.get_document(sample_document)

        assert doc is not None
        assert doc["id"] == sample_document
        assert doc["filename"] == "test_document.pdf"
        assert doc["page_count"] == 5
        assert doc["metadata"]["test"] is True
        assert "upload_date" in doc

    def test_get_nonexistent_document(self, vector_store):
        """Test getting document that doesn't exist"""
        fake_id = str(uuid.uuid4())
        doc = vector_store.get_document(fake_id)

        assert doc is None

    def test_delete_document(self, vector_store):
        """Test deleting a document"""
        # Create document
        doc_id = vector_store.insert_document(
            filename="delete_test.pdf",
            page_count=1
        )

        # Verify it exists
        doc = vector_store.get_document(doc_id)
        assert doc is not None

        # Delete it
        result = vector_store.delete_document(doc_id)
        assert result is True

        # Verify it's gone
        doc = vector_store.get_document(doc_id)
        assert doc is None

    def test_delete_nonexistent_document(self, vector_store):
        """Test deleting document that doesn't exist"""
        fake_id = str(uuid.uuid4())
        result = vector_store.delete_document(fake_id)

        assert result is False

    def test_list_documents(self, vector_store, sample_document):
        """Test listing documents with pagination"""
        docs = vector_store.list_documents(limit=10, offset=0)

        assert isinstance(docs, list)
        assert len(docs) > 0

        # Find our test document
        test_doc = next((d for d in docs if d["id"] == sample_document), None)
        assert test_doc is not None
        assert test_doc["filename"] == "test_document.pdf"


class TestChunkOperations:
    """Test chunk CRUD operations"""

    def test_insert_chunks(self, vector_store, sample_document, embedder):
        """Test inserting chunks with embeddings"""
        texts = ["Test chunk 1", "Test chunk 2"]
        embeddings = embedder.embed_batch(texts)

        chunks = [
            {"text": text, "embedding": emb, "metadata": {"test": True}}
            for text, emb in zip(texts, embeddings)
        ]

        chunk_ids = vector_store.insert_chunks(sample_document, chunks)

        assert len(chunk_ids) == 2
        assert all(len(cid) == 36 for cid in chunk_ids)  # UUID format

    def test_get_document_chunks(self, vector_store, sample_document, sample_chunks):
        """Test retrieving all chunks for a document"""
        chunks = vector_store.get_document_chunks(sample_document)

        assert len(chunks) == 5
        assert all("text" in chunk for chunk in chunks)
        assert all("chunk_index" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)

        # Should be ordered by chunk_index
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i

    def test_get_chunks_with_embeddings(self, vector_store, sample_document, sample_chunks):
        """Test retrieving chunks with embeddings included"""
        chunks = vector_store.get_document_chunks(
            sample_document,
            include_embeddings=True
        )

        assert len(chunks) == 5
        assert all("embedding" in chunk for chunk in chunks)

        # Verify embedding dimensions
        for chunk in chunks:
            assert len(chunk["embedding"]) == 384

    def test_delete_chunks(self, vector_store, sample_document, sample_chunks):
        """Test deleting specific chunks"""
        # Delete first two chunks
        chunks_to_delete = sample_chunks[:2]
        deleted_count = vector_store.delete_chunks(chunks_to_delete)

        assert deleted_count == 2

        # Verify remaining chunks
        remaining_chunks = vector_store.get_document_chunks(sample_document)
        assert len(remaining_chunks) == 3

    def test_chunks_cascade_delete(self, vector_store, embedder):
        """Test that chunks are deleted when document is deleted"""
        # Create document with chunks
        doc_id = vector_store.insert_document("cascade_test.pdf", page_count=1)

        texts = ["Chunk 1", "Chunk 2"]
        embeddings = embedder.embed_batch(texts)
        chunks = [
            {"text": text, "embedding": emb, "metadata": {}}
            for text, emb in zip(texts, embeddings)
        ]
        vector_store.insert_chunks(doc_id, chunks)

        # Verify chunks exist
        doc_chunks = vector_store.get_document_chunks(doc_id)
        assert len(doc_chunks) == 2

        # Delete document
        vector_store.delete_document(doc_id)

        # Chunks should be gone too (CASCADE delete)
        remaining_chunks = vector_store.get_document_chunks(doc_id)
        assert len(remaining_chunks) == 0


class TestVectorSearch:
    """Test vector similarity search"""

    def test_basic_search(self, vector_store, sample_document, sample_chunks, embedder):
        """Test basic similarity search"""
        # Search for vacation-related content
        query = "information about vacation and time off"
        query_vector = embedder.embed(query)

        results = vector_store.search(query_vector, top_k=3)

        assert len(results) > 0
        assert len(results) <= 3

        # Verify result structure
        for result in results:
            assert "text" in result
            assert "similarity" in result
            assert "distance" in result
            assert "chunk_index" in result
            assert "document_id" in result

            # Similarity should be between 0 and 1
            assert 0 <= result["similarity"] <= 1

    def test_search_returns_most_similar(self, vector_store, sample_document, sample_chunks, embedder):
        """Test that search returns most similar chunks"""
        # Search for vacation - should match "vacation benefits" chunk
        query = "paid time off and vacation days"
        query_vector = embedder.embed(query)

        results = vector_store.search(query_vector, top_k=1)

        assert len(results) == 1
        assert "vacation" in results[0]["text"].lower()

    def test_search_with_document_filter(self, vector_store, sample_document, sample_chunks, embedder):
        """Test search filtered by document ID"""
        query = "employee policies"
        query_vector = embedder.embed(query)

        # Search with filter
        results = vector_store.search(
            query_vector,
            top_k=10,
            filters={"document_id": sample_document}
        )

        # All results should be from the specified document
        assert all(r["document_id"] == sample_document for r in results)

    def test_search_top_k_limit(self, vector_store, sample_document, sample_chunks, embedder):
        """Test that top_k parameter limits results"""
        query = "workplace policies"
        query_vector = embedder.embed(query)

        # Search with different top_k values
        results_2 = vector_store.search(query_vector, top_k=2)
        results_5 = vector_store.search(query_vector, top_k=5)

        assert len(results_2) <= 2
        assert len(results_5) <= 5

    def test_search_empty_database(self, vector_store, embedder):
        """Test search when no matching documents exist"""
        # Create a document ID that doesn't exist
        fake_id = str(uuid.uuid4())

        query = "test query"
        query_vector = embedder.embed(query)

        results = vector_store.search(
            query_vector,
            top_k=10,
            filters={"document_id": fake_id}
        )

        assert len(results) == 0

    def test_similarity_scores_ordered(self, vector_store, sample_document, sample_chunks, embedder):
        """Test that results are ordered by similarity (descending)"""
        query = "health insurance coverage"
        query_vector = embedder.embed(query)

        results = vector_store.search(query_vector, top_k=5)

        assert len(results) > 1

        # Verify results are ordered by similarity (highest first)
        similarities = [r["similarity"] for r in results]
        assert similarities == sorted(similarities, reverse=True)


class TestIntegration:
    """Integration tests with full pipeline"""

    def test_full_document_pipeline(self, vector_store, embedder):
        """Test complete workflow: insert document -> add chunks -> search -> delete"""
        # Step 1: Insert document
        doc_id = vector_store.insert_document(
            filename="integration_test.pdf",
            page_count=3,
            metadata={"type": "integration_test"}
        )

        # Step 2: Create and insert chunks
        texts = [
            "Company provides comprehensive health insurance.",
            "Employees receive 20 days of vacation per year.",
            "Remote work is allowed up to 3 days per week."
        ]
        embeddings = embedder.embed_batch(texts)
        chunks = [
            {"text": text, "embedding": emb, "metadata": {"page": i + 1}}
            for i, (text, emb) in enumerate(zip(texts, embeddings))
        ]
        chunk_ids = vector_store.insert_chunks(doc_id, chunks)

        # Step 3: Verify document metadata updated
        doc = vector_store.get_document(doc_id)
        assert doc["chunk_count"] == 3

        # Step 4: Perform search
        query = "how many vacation days do employees get?"
        query_vector = embedder.embed(query)
        results = vector_store.search(query_vector, top_k=1)

        assert len(results) > 0
        assert "vacation" in results[0]["text"].lower()

        # Step 5: Cleanup
        deleted = vector_store.delete_document(doc_id)
        assert deleted is True

        # Verify everything is cleaned up
        doc = vector_store.get_document(doc_id)
        assert doc is None

    def test_concurrent_documents(self, vector_store, embedder):
        """Test handling multiple documents simultaneously"""
        doc_ids = []

        try:
            # Create multiple documents
            for i in range(3):
                doc_id = vector_store.insert_document(
                    filename=f"concurrent_test_{i}.pdf",
                    page_count=1
                )
                doc_ids.append(doc_id)

                # Add chunks to each
                text = f"This is content for document {i}."
                embedding = embedder.embed(text)
                chunks = [{"text": text, "embedding": embedding, "metadata": {}}]
                vector_store.insert_chunks(doc_id, chunks)

            # Search should find chunks from all documents
            query = "content for document"
            query_vector = embedder.embed(query)
            results = vector_store.search(query_vector, top_k=10)

            assert len(results) >= 3

            # Verify results come from different documents
            doc_ids_in_results = set(r["document_id"] for r in results)
            assert len(doc_ids_in_results) >= 2

        finally:
            # Cleanup
            for doc_id in doc_ids:
                vector_store.delete_document(doc_id)


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_document_id(self, vector_store):
        """Test handling of invalid document ID format"""
        with pytest.raises(Exception):
            vector_store.get_document("not-a-valid-uuid")

    def test_insert_chunks_invalid_document(self, vector_store, embedder):
        """Test inserting chunks for non-existent document"""
        fake_id = str(uuid.uuid4())

        text = "Test chunk"
        embedding = embedder.embed(text)
        chunks = [{"text": text, "embedding": embedding, "metadata": {}}]

        with pytest.raises(Exception):
            vector_store.insert_chunks(fake_id, chunks)

    def test_search_wrong_dimension(self, vector_store):
        """Test search with wrong embedding dimension"""
        # Create vector with wrong dimension (should be 384)
        wrong_vector = [0.1] * 100

        with pytest.raises(Exception):
            vector_store.search(wrong_vector, top_k=5)
