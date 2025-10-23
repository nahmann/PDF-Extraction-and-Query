# Vector Store Module

PostgreSQL + pgvector implementation for storing and querying document embeddings.

## Overview

This module provides a complete vector database solution for the RAG pipeline:
- Store PDF documents with metadata
- Store text chunks with vector embeddings
- Perform fast similarity search using cosine distance
- Full CRUD operations for documents and chunks

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Vector Store Layer                     │
├─────────────────────────────────────────────────────────┤
│  PgVectorStore (Client)                                 │
│    ├─ Document Management (CRUD)                        │
│    ├─ Chunk Storage (with embeddings)                   │
│    └─ Similarity Search (cosine distance)               │
├─────────────────────────────────────────────────────────┤
│  SQLAlchemy ORM                                         │
│    ├─ Document Model (metadata)                         │
│    └─ Chunk Model (text + embedding vector)             │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL + pgvector                                  │
│    ├─ JSONB for flexible metadata                       │
│    ├─ VECTOR type for embeddings                        │
│    └─ IVFFLAT index for fast similarity search          │
└─────────────────────────────────────────────────────────┘
```

## Files

- **`base_store.py`**: Abstract base class defining vector store interface
- **`schema.py`**: SQLAlchemy models (Document, Chunk) and database schema
- **`pgvector_client.py`**: PostgreSQL + pgvector implementation
- **`__init__.py`**: Module exports

## Quick Start

### 1. Install Dependencies

```bash
pip install psycopg2-binary sqlalchemy pgvector
```

### 2. Set Up Database

```bash
# Create database
createdb pdf_rag

# Initialize schema
python scripts/init_database.py
```

### 3. Use in Code

```python
from vector_store.pgvector_client import PgVectorStore
from embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder

# Initialize store
store = PgVectorStore(
    connection_string="postgresql://user:pass@localhost:5432/pdf_rag",
    embedding_dim=384
)

# Initialize embedder
embedder = SentenceTransformerEmbedder()

# Insert document
doc_id = store.insert_document(
    filename="example.pdf",
    page_count=10,
    metadata={"category": "manual"}
)

# Insert chunks with embeddings
texts = ["First chunk", "Second chunk"]
embeddings = embedder.embed_batch(texts)
chunks = [
    {"text": text, "embedding": emb, "metadata": {}}
    for text, emb in zip(texts, embeddings)
]
store.insert_chunks(doc_id, chunks)

# Search
query = "example search query"
query_vector = embedder.embed(query)
results = store.search(query_vector, top_k=5)

for result in results:
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Text: {result['text'][:100]}...")
```

## API Reference

### PgVectorStore

#### Initialization

```python
store = PgVectorStore(
    connection_string: str = None,  # Postgres connection string
    embedding_dim: int = 384,        # Embedding dimension (must match model)
    debug: bool = False              # Enable SQL query logging
)
```

#### Document Operations

##### insert_document()
```python
doc_id = store.insert_document(
    filename: str,                    # PDF filename
    page_count: int = None,          # Number of pages
    metadata: Dict[str, Any] = None  # Additional metadata (JSONB)
) -> str  # Returns document UUID
```

##### get_document()
```python
doc = store.get_document(document_id: str) -> Dict[str, Any]
# Returns: {
#     "id": "uuid",
#     "filename": "example.pdf",
#     "page_count": 10,
#     "chunk_count": 25,
#     "metadata": {...},
#     "upload_date": "2024-01-15T10:30:00",
#     "created_at": "2024-01-15T10:30:00"
# }
```

##### list_documents()
```python
docs = store.list_documents(
    limit: int = 100,   # Max results
    offset: int = 0     # Skip N documents
) -> List[Dict[str, Any]]
```

##### delete_document()
```python
success = store.delete_document(document_id: str) -> bool
# Cascades to delete all associated chunks
```

#### Chunk Operations

##### insert_chunks()
```python
chunk_ids = store.insert_chunks(
    document_id: str,
    chunks: List[Dict[str, Any]]  # [{"text": str, "embedding": List[float], "metadata": dict}]
) -> List[str]  # Returns chunk UUIDs
```

##### get_document_chunks()
```python
chunks = store.get_document_chunks(
    document_id: str,
    include_embeddings: bool = False  # Include embedding vectors in results
) -> List[Dict[str, Any]]
```

##### delete_chunks()
```python
deleted_count = store.delete_chunks(chunk_ids: List[str]) -> int
```

#### Search Operations

##### search()
```python
results = store.search(
    query_vector: List[float],           # Query embedding vector
    top_k: int = 10,                     # Number of results to return
    filters: Dict[str, Any] = None       # {"document_id": "uuid"}
) -> List[Dict[str, Any]]

# Returns: [
#     {
#         "id": "chunk_uuid",
#         "document_id": "doc_uuid",
#         "text": "chunk text",
#         "chunk_index": 0,
#         "similarity": 0.85,  # Cosine similarity (0-1)
#         "distance": 0.15,    # Cosine distance (1 - similarity)
#         "metadata": {...},
#         "created_at": "2024-01-15T10:30:00"
#     }
# ]
```

#### Utility Operations

##### initialize_database()
```python
store.initialize_database() -> bool
# Creates extension, tables, and indexes (idempotent)
```

##### get_stats()
```python
stats = store.get_stats() -> Dict[str, Any]
# Returns: {
#     "document_count": 42,
#     "chunk_count": 1337,
#     "embedding_dimension": 384
# }
```

##### close()
```python
store.close()  # Close database connections (cleanup)
```

## Database Schema

### Documents Table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    upload_date TIMESTAMP NOT NULL,
    page_count INTEGER,
    chunk_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Chunks Table
```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector similarity index
CREATE INDEX ix_chunks_embedding_cosine
ON chunks USING ivfflat (embedding vector_cosine_ops);
```

## Performance Considerations

### Index Types

The module uses **IVFFLAT** indexing by default:
- Good for datasets with 1K-1M vectors
- Requires training on existing data
- Fast search with good recall

For larger datasets, consider **HNSW**:
```sql
CREATE INDEX ix_chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Batch Operations

Always use batch operations when inserting multiple items:

```python
# ✓ Good: Batch insert
embeddings = embedder.embed_batch(texts)  # Batch embedding
store.insert_chunks(doc_id, chunks)        # Batch insert

# ✗ Bad: Individual inserts
for text in texts:
    emb = embedder.embed(text)             # Slow
    store.insert_chunks(doc_id, [chunk])   # Many DB calls
```

### Connection Pooling

The store uses SQLAlchemy's connection pooling:
- Configure pool size via `settings.db_pool_size`
- Connections are reused automatically
- Always call `store.close()` when done

## Error Handling

```python
from sqlalchemy.exc import SQLAlchemyError

try:
    doc_id = store.insert_document("test.pdf")
except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    # Handle error (rollback is automatic)
```

## Testing

Run vector store tests:

```bash
# Set up test database
createdb pdf_rag_test
export DATABASE_URL="postgresql://user:pass@localhost:5432/pdf_rag_test"

# Run tests
python -m pytest tests/unit/test_vector_store.py -v
```

## Configuration

Environment variables (in `.env`):

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/pdf_rag
DB_POOL_SIZE=10        # Connection pool size
DB_ECHO=false          # Log SQL queries
EMBEDDING_DIMENSION=384  # Must match your embedding model
```

## Examples

### Example 1: Process and Store a PDF

```python
from extraction.pymupdf_extractor import PyMuPDFExtractor
from cleaning.text_cleaner import TextCleaner
from chunking.langchain_chunker import LangChainChunker
from embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
from vector_store.pgvector_client import PgVectorStore

# Initialize components
extractor = PyMuPDFExtractor()
cleaner = TextCleaner()
chunker = LangChainChunker()
embedder = SentenceTransformerEmbedder()
store = PgVectorStore()

# Process PDF
result = extractor.extract("document.pdf")
cleaned, _ = cleaner.clean(result.extracted_text)
chunks = chunker.chunk(cleaned)

# Generate embeddings
texts = [chunk['text'] for chunk in chunks]
embeddings = embedder.embed_batch(texts)

# Store in database
doc_id = store.insert_document(
    filename="document.pdf",
    page_count=result.metadata['page_count']
)

chunks_with_embeddings = [
    {**chunk, "embedding": emb}
    for chunk, emb in zip(chunks, embeddings)
]
store.insert_chunks(doc_id, chunks_with_embeddings)
```

### Example 2: Search Across Multiple Documents

```python
# Search without document filter (all documents)
query = "What is the vacation policy?"
query_vector = embedder.embed(query)

results = store.search(query_vector, top_k=10)

for result in results:
    doc = store.get_document(result['document_id'])
    print(f"From: {doc['filename']}")
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Text: {result['text'][:200]}...")
    print()
```

### Example 3: Update Document Metadata

```python
# Get document
doc = store.get_document(doc_id)

# Update metadata (requires manual SQL or retrieve->modify->update pattern)
# Note: Direct metadata update not implemented in base client
# You can extend the client or use raw SQL:

from sqlalchemy import text
with store.engine.connect() as conn:
    conn.execute(
        text("UPDATE documents SET metadata = :meta WHERE id = :id"),
        {"meta": new_metadata, "id": doc_id}
    )
    conn.commit()
```

## Extending the Store

To add custom functionality, extend `PgVectorStore`:

```python
from vector_store.pgvector_client import PgVectorStore

class CustomVectorStore(PgVectorStore):
    def search_with_reranking(self, query_vector, top_k=10):
        """Custom search with reranking logic"""
        # Get initial results
        initial_results = self.search(query_vector, top_k=top_k * 2)

        # Apply custom reranking
        reranked = self._rerank(initial_results)

        return reranked[:top_k]

    def _rerank(self, results):
        # Custom reranking logic
        return sorted(results, key=lambda r: r['custom_score'], reverse=True)
```

## See Also

- [VECTOR_STORE_SETUP.md](../../docs/VECTOR_STORE_SETUP.md) - Setup guide
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
