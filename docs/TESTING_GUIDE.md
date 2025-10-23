# RAG Pipeline Testing Guide

This guide explains how to test the complete RAG (Retrieval-Augmented Generation) pipeline.

## Quick Start

```bash
# 1. Start the database (if not running)
cd database
docker-compose up -d
cd ..

# 2. Run interactive test (uploads PDFs and starts query interface)
python test_interactive_search.py
```

That's it! The script will:
- Upload all PDFs from the sample folder
- Start an interactive query interface
- Let you test different questions and see results

## Interactive Testing Features

### Basic Queries
Just type your question naturally:
```
Query: What are the stock option vesting terms?
Query: What is the salary mentioned in the offer letter?
Query: Who are the parties in the incentive plan?
```

### Commands
- `list` - Show all uploaded documents
- `top 5` - Change number of results (default is 3)
- `chunk <doc_id> <chunk_num>` - View full text of a specific chunk
- `quit` or `exit` - Exit the program

### Example Session
```
[top 3] Query: What are the vesting terms?

[Result 1] Similarity: 0.8523
Document: deepshield-systems-inc-equity-incentive-plan.pdf
Chunk: #5
Document ID: abc-123-def-456
----------------------------------------------------------------------
The vesting schedule for stock options shall be as follows...
----------------------------------------------------------------------

[top 3] Query: top 5
✓ Now showing top 5 results

[top 5] Query: chunk abc-123-def-456 5
======================================================================
Chunk #5 from deepshield-systems-inc-equity-incentive-plan.pdf
======================================================================
[Full chunk text displayed here]
======================================================================

[top 5] Query: quit
```

## Testing Strategies

### 1. Test Query Variations
Try asking the same question different ways to see how semantic search handles variations:
```
Query: What is the base salary?
Query: How much does the position pay?
Query: What are the compensation details?
```

### 2. Test Different Document Types
Upload different PDFs to see how the system handles various content:
```bash
# Upload custom folder
python test_interactive_search.py --folder "path/to/your/pdfs"
```

### 3. Test Chunk Quality
Use the `chunk` command to view full chunks and verify:
- Is the chunk size appropriate?
- Does the chunk have complete information?
- Is the overlap working correctly?

```
Query: chunk <doc_id> 0
```

### 4. Test Without Re-uploading
If documents are already in the database, skip upload:
```bash
python test_interactive_search.py --skip-upload
```

## Database Management

### View Database Statistics
```bash
python scripts/manage_database.py --stats
```

Shows:
- Number of documents and chunks
- Database size
- Table sizes (documents, chunks, indexes)
- List of all documents

### Clear Database (Fresh Start)
```bash
python scripts/manage_database.py --clear
```

Useful when:
- Testing different chunking parameters
- Starting over with new documents
- Cleaning up after experiments

### Delete Specific Document
```bash
python scripts/manage_database.py --delete-document <doc_id>
```

Useful when:
- Removing a problematic document
- Testing with fewer documents
- Cleaning up individual uploads

### Reclaim Disk Space
```bash
python scripts/manage_database.py --vacuum
```

Useful when:
- After deleting many documents
- Database has grown large
- Periodic maintenance

## Database Growth & Cleanup FAQ

### Will the database fill up during testing?
Yes, each PDF upload creates:
- 1 document record
- N chunk records (depends on document size)
- N embeddings (384 dimensions each)

Example sizes:
- Small PDF (5 pages): ~10 chunks = ~40KB
- Medium PDF (20 pages): ~50 chunks = ~200KB
- Large PDF (100 pages): ~250 chunks = ~1MB

### Should I clear between tests?
**It depends on what you're testing:**

#### ✅ Clear database when:
- **Changing chunking parameters** (chunk size, overlap)
  - Otherwise you'll have duplicates with different chunking
- **Testing different extraction methods**
  - To compare results cleanly
- **Starting a fresh experiment**
  - To avoid confusion with old data

#### ❌ Don't clear when:
- **Testing different queries** on same documents
  - Uploading is slow, querying is fast
  - Keep documents and just query different ways
- **Adding more documents** to test multi-document search
  - Database handles duplicates fine (different document IDs)
- **Experimenting with query variations**
  - No need to re-upload

### Can I upload the same PDF multiple times?
Yes! Each upload creates a new document with a unique ID. This is actually useful for:
- Comparing different processing methods
- Testing with and without cleaning
- Experimenting with chunk parameters

The database won't merge them - each upload is separate.

### What if I want to replace a document?
Two options:

1. **Delete old, upload new:**
   ```bash
   # Find document ID
   python scripts/list_documents.py

   # Delete old version
   python scripts/manage_database.py --delete-document <doc_id>

   # Upload new version
   python scripts/upload_pdf.py document.pdf
   ```

2. **Clear all and re-upload:**
   ```bash
   python scripts/manage_database.py --clear
   python test_interactive_search.py
   ```

### Recommended workflow

**For daily testing (same documents, different queries):**
```bash
# Once: Upload documents
python test_interactive_search.py

# Many times: Just query (skip upload)
python test_interactive_search.py --skip-upload
```

**For experimentation (changing chunking/cleaning):**
```bash
# 1. Clear database
python scripts/manage_database.py --clear

# 2. Modify chunking parameters in code
# Edit src/chunking/langchain_chunker.py or test_interactive_search.py

# 3. Upload with new parameters
python test_interactive_search.py
```

**For comparing approaches:**
```bash
# Upload same PDFs with different settings
# Each upload gets unique ID, so you can compare results

# Method 1: Default settings
python test_interactive_search.py

# Method 2: Different chunk size
# (modify code, then upload - they won't conflict)
python test_interactive_search.py
```

## Advanced Testing

### Test with Verbose Output
See detailed processing steps:
```bash
python test_interactive_search.py --verbose
```

### Test Individual Scripts
For more control, use individual scripts:

```bash
# Upload one document
python scripts/upload_pdf.py document.pdf --verbose

# Query all documents
python scripts/query_documents.py "your question" --top-k 5 --verbose

# List all documents
python scripts/list_documents.py --verbose
```

## Evaluating Search Quality

### Good Results (High Similarity Score)
- Similarity > 0.7: Highly relevant
- Similarity 0.5-0.7: Moderately relevant
- Similarity < 0.5: Weakly relevant

### Signs of Good Chunking
- Chunks contain complete thoughts/paragraphs
- Important information isn't split mid-sentence
- Chunks have enough context to be meaningful alone

### Signs of Bad Chunking
- Sentences cut off mid-thought
- Chunks too small (< 200 chars) - not enough context
- Chunks too large (> 3000 chars) - too broad, reduces precision

### Testing Chunk Quality
1. Run a query
2. Look at top result
3. Use `chunk <doc_id> <chunk_num>` to see full chunk
4. Ask yourself:
   - Does this chunk answer the question?
   - Is there enough context?
   - Are related sentences included?

## Troubleshooting

### Database not running
```bash
cd database
docker-compose up -d
cd ..
```

### Connection errors
Check if native PostgreSQL is running (conflicts with Docker):
```bash
# Windows
netstat -ano | findstr ":5432"

# If native PostgreSQL is running, stop it:
cd database
stop_native_postgres.bat
```

### Out of memory during embedding
Reduce batch size in code or process fewer documents.

### Slow queries
- Check database stats: `python scripts/manage_database.py --stats`
- Ensure IVFFLAT index is created (happens after ~1000 chunks)
- Consider vacuuming: `python scripts/manage_database.py --vacuum`

## Tips for Best Results

1. **Start small**: Test with 2-3 documents first
2. **Try variations**: Ask the same question multiple ways
3. **Check chunks**: Use `chunk` command to see what was captured
4. **Iterate**: Adjust chunking parameters based on results
5. **Clean between experiments**: Clear database when changing chunking strategy
6. **Keep documents for queries**: Don't clear if just testing different questions

## Next Steps

Once you're happy with results:
1. Use these scripts as reference for building FastAPI routes
2. The core functions in scripts can be imported directly
3. Add authentication, rate limiting, etc. for production
