# API Quick Start Guide

## 5-Minute Setup

### 1. Start Database
```bash
cd database
docker-compose up -d
cd ..
```

### 2. Start API
```bash
uvicorn src.api.main:app --reload
```

### 3. Open Browser
Go to: **http://localhost:8000/docs**

You'll see the interactive Swagger UI where you can test all endpoints!

---

## Test the API (3 Commands)

### 1. Upload a Document
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@tests/fixtures/sample_pdfs/deepshield-systems-inc/company-profile.pdf"
```

### 2. Search Documents
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What does DeepShield do?", "top_k": 3}'
```

### 3. List Documents
```bash
curl "http://localhost:8000/api/v1/documents"
```

---

## M&A Due Diligence Scenario

### Bulk Upload (Upload all 490 PDFs)

```python
# save as upload_all.py
import requests
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"
folder = Path("tests/fixtures/sample_pdfs/deepshield-systems-inc")

for pdf in folder.rglob("*.pdf"):
    print(f"Uploading {pdf.name}...")
    with open(pdf, "rb") as f:
        response = requests.post(
            f"{API_BASE}/documents/upload",
            files={"file": f}
        )
    if response.status_code == 201:
        print(f"  ✓ {response.json()['chunk_count']} chunks")
    else:
        print(f"  ✗ Error: {response.json()}")
```

Run it:
```bash
python upload_all.py
```

### Ask M&A Questions

```python
import requests

API_BASE = "http://localhost:8000/api/v1"

questions = [
    "What are the Series C funding terms?",
    "Who are the board members?",
    "What is the stock option vesting schedule?",
    "Do contracts have change of control clauses?",
    "What patents does the company own?",
]

for q in questions:
    print(f"\nQ: {q}")
    response = requests.post(
        f"{API_BASE}/search",
        json={"query": q, "top_k": 1}
    )
    result = response.json()["results"][0]
    print(f"A: {result['text'][:200]}...")
    print(f"   From: {result['document_name']} (similarity: {result['similarity']:.2f})")
```

---

## Evaluation

See `evaluation/ma_test_queries.json` for 40 M&A due diligence test questions.

Test each query and rate the results:
- **4**: Perfect answer
- **3**: Good answer
- **2**: Relevant but incomplete
- **1**: Partially relevant
- **0**: Wrong/irrelevant

---

## Next Steps

1. ✅ API is working
2. ⏭️ Test with M&A queries from `evaluation/ma_test_queries.json`
3. ⏭️ Evaluate chunk quality
4. ⏭️ Switch to Bedrock embeddings (if needed)
5. ⏭️ Build frontend or integrate with existing tools

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.
