# Chunking Strategy Change

**Date:** 2025-10-20
**Reason:** Evaluation showed chunks averaging 215 chars (too small for complete answers)

## What Changed

### Before (LangChain Section-Aware Chunking)
- **Strategy:** Split by document sections/headers first, then by size if needed
- **Config:** max_chunk_size = 2000, overlap = 200
- **Reality:** Avg chunk size = 215 chars (sections were naturally small)
- **Problem:** Most chunks incomplete, low similarity scores (avg 0.58)

### After (Simple Size-Based Chunking)
- **Strategy:** Fixed-size sliding window, ignores document structure
- **Config:** max_chunk_size = 1000, overlap = 200
- **Expected:** Avg chunk size ~800-1000 chars (more consistent)
- **Benefit:** Chunks large enough to contain complete information

## Files Changed

### 1. New Files Created
- **`src/chunking/simple_chunker.py`** - Simple and SmartSimple chunkers
- **`src/chunking/factory.py`** - Chunker factory function
- **`scripts/reprocess_all_documents.py`** - Re-upload all PDFs

### 2. Modified Files
- **`src/config/settings.py`**
  - Changed `max_chunk_size` from 2000 → 1000
  - Added `chunker_type` setting (default: "simple")

- **`src/chunking/__init__.py`**
  - Added SimpleChunker, SmartSimpleChunker, create_chunker exports

- **`src/api/services/rag_service.py`**
  - Now uses `create_chunker()` factory instead of hardcoded LangChainChunker
  - Logs chunker type on initialization

## Available Chunkers

### 1. langchain_simple (DEFAULT - RECOMMENDED)
```python
chunker_type = "langchain_simple"
```
- Size-based with smart boundaries
- Uses LangChain's RecursiveCharacterTextSplitter
- Tries to split at: paragraphs → lines → sentences → words
- Most predictable, consistent chunks
- Best for RAG applications

### 2. langchain (Section-Aware - Original)
```python
chunker_type = "langchain"
```
- Section-aware splitting
- Preserves document structure
- Variable chunk sizes (can be very small or very large)
- Use when document structure is critical

## How to Switch Chunkers

### Via Environment Variable
```bash
export CHUNKER_TYPE="langchain_simple"  # Default (recommended)
export CHUNKER_TYPE="langchain"         # Section-aware
export MAX_CHUNK_SIZE="1000"
export CHUNK_OVERLAP="200"
```

### Via Code
```python
from chunking import create_chunker

# Use default from settings (langchain_simple)
chunker = create_chunker()

# Override settings
chunker = create_chunker(
    chunker_type="langchain",  # Switch to section-aware
    max_chunk_size=800,
    chunk_overlap=150
)
```

## Re-processing Documents

To apply the new chunking strategy to existing documents:

```bash
# This will DELETE all current documents and re-upload with new chunking!
python scripts/reprocess_all_documents.py
```

**WARNING:** This deletes all documents and chunks from the database first!

### What the script does:
1. Shows current config and asks for confirmation
2. Deletes all documents and chunks
3. Finds all PDFs in `data/documents/`
4. Re-processes each with new chunking strategy
5. Shows summary statistics

### Dry run / Check config:
```bash
# See what would happen without actually doing it
python -c "from config.settings import settings; print(f'Chunker: {settings.chunker_type}, Size: {settings.max_chunk_size}')"
```

## Expected Results

### Chunk Statistics (Before)
- Avg chunk size: 215 chars
- Distribution: 80% under 300 chars
- Similarity scores: Avg 0.580 (moderate)
- Top-1 excellent (>0.8): 0/17 queries

### Chunk Statistics (After) - Expected
- Avg chunk size: ~800-1000 chars
- Distribution: Most between 800-1000 chars (consistent)
- Similarity scores: Should improve (more context)
- Top-1 excellent: Hopefully >5/17 queries

## Testing New Results

After re-processing, re-run evaluation:

```bash
# Test critical queries again
python scripts/evaluate_queries.py --priority critical --output evaluation/results_simple_chunker.json

# Analyze results
python scripts/analyze_results.py evaluation/results_simple_chunker.json

# Compare to old results
diff evaluation/results_20251020_232926.json evaluation/results_simple_chunker.json
```

### What to compare:
1. **Avg chunk size** - should be ~800-1000 vs 215
2. **Similarity scores** - should improve (more context to match)
3. **Manual scoring** - chunks should contain more complete answers
4. **Search time** - may be slightly slower (more text to embed)

## Rollback Plan

If new chunking doesn't improve results:

### Option 1: Adjust chunk size
```bash
export MAX_CHUNK_SIZE="1500"  # Larger chunks
# or
export MAX_CHUNK_SIZE="600"   # Smaller chunks
python scripts/reprocess_all_documents.py
```

### Option 2: Revert to section-aware mode
```bash
export CHUNKER_TYPE="langchain"
export MAX_CHUNK_SIZE="2000"
python scripts/reprocess_all_documents.py
```

## Configuration Best Practices

### For Corporate/Legal Documents (Current Use Case)
- **Chunker:** `langchain_simple` (RECOMMENDED)
- **Size:** 800-1200 chars
- **Overlap:** 150-200 chars
- **Why:** Consistent chunks, complete clauses/sentences, splits at natural boundaries

### For Technical Documentation
- **Chunker:** `langchain` (section-aware)
- **Size:** 1500-2000 chars
- **Overlap:** 200 chars
- **Why:** Preserve code blocks, section structure

### For Short-Form Content (Articles, Emails)
- **Chunker:** `langchain_simple`
- **Size:** 400-600 chars
- **Overlap:** 100 chars
- **Why:** Documents already short, need smaller chunks

## Notes

- **API Server:** Restart after changing chunking config
- **Database:** Must re-process all documents to apply new chunking
- **Embeddings:** Changing chunk size changes what gets embedded
- **Comparison:** Keep old evaluation results to compare before/after

## References

- Original evaluation: `evaluation/results_20251020_232926.json`
- Analysis: Showed 215 char avg, 0.58 similarity
- Decision: Switch to size-based chunking for consistency
