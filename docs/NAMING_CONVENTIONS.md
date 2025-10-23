# API Field Naming Conventions

This document establishes the standard field names used throughout the RAG system to ensure consistency.

## Standard Field Names

### Similarity Scores
- **Standard:** `similarity` (float, 0-1, higher is better)
- **Alternative:** `distance` (float, 0+, lower is better) - only used internally
- **DEPRECATED:** `similarity_score` ❌

**Where used:**
- API Response: `SearchResult.similarity`
- Vector Store: `pgvector_client.search()` returns `similarity`
- RAG Service: `search_documents()` returns `similarity`

### Chunk Counts
- **Standard:** `chunk_count` (integer)
- **DEPRECATED:** `total_chunks` ❌

**Where used:**
- API Response: `DocumentInfo.chunk_count`, `StatsResponse.total_chunks`
- Vector Store: `pgvector_client.get_stats()` returns `chunk_count`
- RAG Service: All methods use `chunk_count`

**NOTE:** `StatsResponse.total_chunks` is an exception because it refers to the total across ALL documents, not a single document. This is acceptable.

### Document Counts
- **Standard:** `document_count` (integer) - internal
- **Standard:** `total_documents` (integer) - API response for total count
- **Standard:** `total` (integer) - API response for paginated lists

**Where used:**
- Vector Store: `get_stats()` returns `document_count`
- API Response: `StatsResponse.total_documents`, `DocumentListResponse.total`

### Location Information
- **Standard:** `chunk_index` (integer, 0-based index within document)
- **DEPRECATED:** `page_number` ❌ (we don't reliably track page numbers)

**Where used:**
- API Response: `SearchResult.chunk_index`
- Vector Store: Chunks have `chunk_index` field
- RAG Service: Uses `chunk_index`

## Data Flow

### Search Results Flow

1. **pgvector_client.search()** returns:
```python
{
    'text': str,
    'document_id': str,
    'chunk_index': int,
    'similarity': float,  # ✓ Standardized
    'distance': float,
    'metadata': dict
}
```

2. **rag_service.search_documents()** enriches and returns:
```python
{
    'text': str,
    'document_name': str,
    'document_id': str,
    'relative_path': str,
    'chunk_index': int,      # ✓ Standardized
    'similarity': float,      # ✓ Standardized
    'metadata': dict
}
```

3. **API SearchResult schema** (Pydantic):
```python
{
    'text': str,
    'document_name': str,
    'document_id': str,
    'relative_path': str,
    'chunk_index': int,      # ✓ Standardized
    'similarity': float,      # ✓ Standardized
    'metadata': dict
}
```

### Stats Flow

1. **pgvector_client.get_stats()** returns:
```python
{
    'document_count': int,   # ✓ Standardized
    'chunk_count': int,      # ✓ Standardized
    'embedding_dimension': int
}
```

2. **rag_service.get_stats()** transforms to:
```python
{
    'total_documents': int,  # ✓ Acceptable (refers to total)
    'total_chunks': int,     # ✓ Acceptable (refers to total)
    'database_size': str,
    'avg_chunks_per_document': float
}
```

3. **API StatsResponse schema**:
```python
{
    'total_documents': int,  # ✓ Acceptable
    'total_chunks': int,     # ✓ Acceptable
    'database_size': str,
    'avg_chunks_per_document': float
}
```

## Known Issues (FIXED)

### ✓ Issue 1: Stats endpoint field mismatch
**Status:** FIXED
**Details:** `rag_service.get_stats()` was trying to access `stats['total_chunks']` but pgvector returns `stats['chunk_count']`
**Fix:** Changed rag_service to use `stats['chunk_count']` and rename to `total_chunks` in the response

### ✓ Issue 2: Evaluation script field mismatch
**Status:** FIXED
**Details:** `evaluate_queries.py` was looking for `similarity_score` instead of `similarity`
**Fix:** Updated script to use `similarity` and `chunk_index`

### ✓ Issue 3: Document ID field inconsistency
**Status:** DOCUMENTED (Intentional difference)
**Details:**
- `pgvector_client.list_documents()` returns `doc['id']` (from Document.to_dict())
- API and most code use `document_id`
- Both refer to the same UUID, just different field names in different contexts

**Reasoning:**
- Database layer uses `id` (standard SQL convention)
- API/services use `document_id` (clearer in context with chunks)

**Fix:** Scripts must use `doc['id']` when calling `list_documents()` directly

## Validation Checklist

When adding new features, ensure:

- [ ] Use `similarity` (not `similarity_score`) for cosine similarity scores
- [ ] Use `chunk_count` internally, `total_chunks` only for aggregate stats
- [ ] Use `chunk_index` (not `page_number`) for chunk location
- [ ] Use `document_count` internally, `total_documents` or `total` in API responses
- [ ] Document any exceptions to these conventions with clear rationale

## Reference: All Field Names

### Search Results
| Field | Type | Description | Standard? |
|-------|------|-------------|-----------|
| `text` | str | Chunk content | ✓ |
| `document_name` | str | Filename | ✓ |
| `document_id` | str | UUID | ✓ |
| `relative_path` | str | File path | ✓ |
| `chunk_index` | int | Position in doc | ✓ |
| `similarity` | float | 0-1 score | ✓ |
| `metadata` | dict | Extra data | ✓ |

### Document Info
| Field | Type | Description | Standard? | Notes |
|-------|------|-------------|-----------|-------|
| `id` | str | UUID | ✓ | Database layer only (from list_documents) |
| `document_id` | str | UUID | ✓ | API/service layer (same UUID, different name) |
| `filename` | str | Original name | ✓ | |
| `upload_date` | str | ISO timestamp | ✓ | |
| `page_count` | int | PDF pages | ✓ | |
| `chunk_count` | int | Chunks in doc | ✓ | |
| `metadata` | dict | Extra data | ✓ | |

### Statistics
| Field | Type | Description | Standard? |
|-------|------|-------------|-----------|
| `total_documents` | int | All docs in DB | ✓ |
| `total_chunks` | int | All chunks in DB | ✓ |
| `database_size` | str | Size string | ✓ |
| `avg_chunks_per_document` | float | Average | ✓ |

## Examples

### Correct Usage ✓
```python
# Search result
result = {
    'similarity': 0.85,      # ✓ Good
    'chunk_index': 12        # ✓ Good
}

# Stats
stats = {
    'total_chunks': 4500,    # ✓ Good (aggregate)
    'chunk_count': 15        # ✓ Good (per document)
}
```

### Incorrect Usage ❌
```python
# Search result
result = {
    'similarity_score': 0.85,  # ❌ Bad - use 'similarity'
    'page_number': 5           # ❌ Bad - use 'chunk_index'
}

# Mixing conventions
stats = {
    'total_chunks': count,     # When it should be chunk_count
    'chunk_count': total       # When it should be total_chunks
}
```

## Migration Notes

If you find deprecated field names in existing code:

1. Check if it's in a script (backward compat may be OK)
2. For API changes, update and document in CHANGELOG
3. For internal changes, just fix and test
4. Update this document

Last Updated: 2025-10-20
