# RAG Document Search API Documentation

## Overview

RESTful API for semantic document search using vector embeddings and pgVector. Upload PDFs, extract text, generate embeddings, and perform natural language queries.

**Base URL:** `http://localhost:8000`

**API Version:** 1.0.0

**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)

## Getting Started

### 1. Start the Database

```bash
cd database
docker-compose up -d
cd ..
```

### 2. Start the API

```bash
# Install dependencies (if needed)
pip install fastapi uvicorn python-multipart

# Run the server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test Health Endpoint

```bash
curl http://localhost:8000/api/v1/health
```

## Endpoints

### Health Check

**GET** `/api/v1/health`

Check API and service health status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "embedder": "loaded",
  "timestamp": "2025-10-17T12:00:00"
}
```

---

### Upload Document

**POST** `/api/v1/documents/upload`

Upload and process a PDF document through the RAG pipeline.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@equity-incentive-plan.pdf"
```

**Response:**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "equity-incentive-plan.pdf",
  "page_count": 25,
  "chunk_count": 42,
  "status": "completed",
  "processing_time_ms": 2345
}
```

**Processing Steps:**
1. Extract text using FormattingExtractor
2. Clean extracted text
3. Create chunks (section-aware, 2000 char max)
4. Generate embeddings (sentence-transformers)
5. Store in pgVector database

**Timing:** ~1-3 seconds for typical documents

---

### Search Documents

**POST** `/api/v1/search`

Perform semantic search across all uploaded documents.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the stock option vesting terms?",
    "top_k": 3
  }'
```

**Request Body:**
```json
{
  "query": "What are the stock option vesting terms?",
  "top_k": 3,
  "document_id": "optional-uuid-filter"
}
```

**Response:**
```json
{
  "query": "What are the stock option vesting terms?",
  "results": [
    {
      "text": "Stock options vest over four years with a one-year cliff. 25% of the shares vest after the first year, with the remaining 75% vesting monthly thereafter (1/48th per month).",
      "document_name": "equity-incentive-plan.pdf",
      "document_id": "123e4567-e89b-12d3-a456-426614174000",
      "relative_path": "Legal & Insurance/equity-incentive-plan.pdf",
      "chunk_index": 5,
      "similarity": 0.8523,
      "metadata": {
        "section": "Vesting Schedule",
        "is_split_chunk": false
      }
    },
    {
      "text": "...",
      "similarity": 0.7821,
      ...
    }
  ],
  "total_results": 3,
  "search_time_ms": 145
}
```

**Similarity Scores:**
- **0.8-1.0**: Highly relevant
- **0.6-0.8**: Moderately relevant
- **0.4-0.6**: Weakly relevant
- **< 0.4**: Likely not relevant

---

### List Documents

**GET** `/api/v1/documents?limit=100&offset=0`

List all uploaded documents with pagination.

**Query Parameters:**
- `limit` (int): Max results to return (default: 100, max: 1000)
- `offset` (int): Number to skip for pagination (default: 0)

**Request:**
```bash
curl "http://localhost:8000/api/v1/documents?limit=10&offset=0"
```

**Response:**
```json
{
  "documents": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "equity-incentive-plan.pdf",
      "upload_date": "2025-10-17T12:00:00",
      "page_count": 25,
      "chunk_count": 42,
      "metadata": {
        "relative_path": "Legal & Insurance/equity-incentive-plan.pdf",
        "extraction_method": "FormattingExtractor",
        "cleaning_warnings": 0
      }
    }
  ],
  "total": 490
}
```

---

### Get Document

**GET** `/api/v1/documents/{document_id}`

Get detailed information about a specific document.

**Request:**
```bash
curl "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000"
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "equity-incentive-plan.pdf",
  "upload_date": "2025-10-17T12:00:00",
  "page_count": 25,
  "chunk_count": 42,
  "metadata": {
    "relative_path": "Legal & Insurance/equity-incentive-plan.pdf",
    "extraction_method": "FormattingExtractor"
  }
}
```

---

### Delete Document

**DELETE** `/api/v1/documents/{document_id}`

Delete a document and all its chunks.

**Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000"
```

**Response:**
```json
{
  "deleted": true,
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "chunks_deleted": 42
}
```

**Warning:** This operation cannot be undone!

---

### Database Statistics

**GET** `/api/v1/stats`

Get overall database statistics.

**Request:**
```bash
curl "http://localhost:8000/api/v1/stats"
```

**Response:**
```json
{
  "total_documents": 490,
  "total_chunks": 8532,
  "database_size": "125 MB",
  "avg_chunks_per_document": 17.4
}
```

---

## M&A Due Diligence Use Case

### Scenario
You're evaluating DeepShield Systems Inc. for acquisition. They've provided 490 PDFs across 8 categories. Use the API to quickly extract insights before meetings.

### Example Queries

#### Corporate Structure
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who are the current board members?", "top_k": 3}'
```

#### Funding Terms
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the Series C funding terms and liquidation preferences?", "top_k": 5}'
```

#### Employee Equity
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the stock option vesting schedule and acceleration clauses?", "top_k": 3}'
```

#### Customer Contracts
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Do customer contracts have change of control provisions?", "top_k": 5}'
```

#### IP & Technology
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What patents and proprietary technology does the company own?", "top_k": 5}'
```

#### Liabilities
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Are there any pending lawsuits or regulatory investigations?", "top_k": 3}'
```

See `evaluation/ma_test_queries.json` for complete list of 40 M&A due diligence queries.

---

## Error Handling

All endpoints return appropriate HTTP status codes and error details.

### Error Response Format
```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "timestamp": "2025-10-17T12:00:00"
}
```

### Common HTTP Status Codes

- **200 OK**: Successful request
- **201 Created**: Resource created (document upload)
- **400 Bad Request**: Invalid input (wrong file type, invalid parameters)
- **404 Not Found**: Resource doesn't exist (document ID not found)
- **500 Internal Server Error**: Server-side error (database down, processing failed)

---

## Python Client Examples

### Upload and Search Workflow

```python
import requests

API_BASE = "http://localhost:8000/api/v1"

# 1. Upload a document
with open("equity-incentive-plan.pdf", "rb") as f:
    response = requests.post(
        f"{API_BASE}/documents/upload",
        files={"file": f}
    )
    doc_id = response.json()["document_id"]
    print(f"Uploaded: {doc_id}")

# 2. Search documents
response = requests.post(
    f"{API_BASE}/search",
    json={
        "query": "What are the vesting terms?",
        "top_k": 3
    }
)
results = response.json()

for i, result in enumerate(results["results"], 1):
    print(f"\n[Result {i}] Similarity: {result['similarity']:.4f}")
    print(f"Document: {result['document_name']}")
    print(f"Text: {result['text'][:200]}...")

# 3. List all documents
response = requests.get(f"{API_BASE}/documents?limit=10")
docs = response.json()
print(f"\nTotal documents: {docs['total']}")

# 4. Get stats
response = requests.get(f"{API_BASE}/stats")
stats = response.json()
print(f"\nDatabase: {stats['database_size']}")
print(f"Documents: {stats['total_documents']}")
print(f"Chunks: {stats['total_chunks']}")
```

### Batch Upload

```python
import requests
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"

# Upload all PDFs from a folder
pdf_folder = Path("tests/fixtures/sample_pdfs/deepshield-systems-inc")
uploaded = []

for pdf_file in pdf_folder.rglob("*.pdf"):
    print(f"Uploading: {pdf_file.name}")

    with open(pdf_file, "rb") as f:
        response = requests.post(
            f"{API_BASE}/documents/upload",
            files={"file": (pdf_file.name, f, "application/pdf")}
        )

    if response.status_code == 201:
        result = response.json()
        uploaded.append(result)
        print(f"  ✓ {result['chunk_count']} chunks, {result['processing_time_ms']}ms")
    else:
        print(f"  ✗ Failed: {response.json()}")

print(f"\nUploaded {len(uploaded)} documents")
```

---

## Performance

### Typical Response Times

- **Health check**: < 50ms
- **Document list**: < 100ms
- **Search query**: 100-300ms (depends on database size)
- **Document upload**: 1-5 seconds (depends on PDF size)
- **Document deletion**: < 100ms

### Optimization Tips

1. **Batch uploads**: Use async/concurrent uploads for multiple files
2. **Adjust top_k**: Lower values (3-5) are faster than 10-20
3. **Database indexing**: Ensure IVFFLAT index is created (auto after ~1000 chunks)
4. **Filter by document_id**: Speeds up search when you know the source document

---

## Development & Testing

### Run Tests
```bash
pytest tests/api/test_endpoints.py -v
```

### Access Interactive Docs
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Enable Debug Mode
```python
# In main.py
app.debug = True  # Shows detailed error messages
```

### Monitor Logs
```bash
# API logs to stdout
uvicorn src.api.main:app --reload --log-level debug
```

---

## Production Deployment

### Environment Variables

Create `.env` file:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pdf_rag
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
MAX_CHUNK_SIZE=2000
CHUNK_OVERLAP=200
```

### Run with Gunicorn (Production)

```bash
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
CMD ["gunicorn", "src.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

---

## Next Steps

1. **Test with M&A queries**: Use `evaluation/ma_test_queries.json`
2. **Bedrock integration**: Switch to AWS Bedrock embeddings
3. **Add authentication**: JWT tokens, API keys
4. **Rate limiting**: Prevent abuse
5. **Async processing**: Background jobs for large uploads
6. **Answer generation**: Add LLM-powered answer synthesis

---

## Support & Documentation

- **API Docs**: `http://localhost:8000/docs`
- **GitHub**: [Repository link]
- **Email**: [Support email]

## License

[Your license]
