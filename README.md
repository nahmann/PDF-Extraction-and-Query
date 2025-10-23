# PDF RAG System for M&A Due Diligence

A production-ready PDF processing pipeline for RAG (Retrieval-Augmented Generation) systems, optimized for M&A due diligence document analysis. Extracts text from PDFs, generates embeddings, stores vectors, and provides semantic search capabilities.

## 🎯 Project Overview

This system transforms PDF documents into searchable, AI-ready knowledge bases optimized for complex business queries. Built specifically for M&A due diligence use cases.

### Key Features

- ✅ **Multi-Strategy PDF Extraction** - PyMuPDF with fallback to AWS Textract
- ✅ **Intelligent Text Preprocessing** - Section-aware parsing, header detection, cleaning
- ✅ **Optimized Chunking** - Section-aware strategy proven to deliver 11% better similarity scores
- ✅ **Local Embeddings** - sentence-transformers/all-MiniLM-L6-v2 (no external API needed)
- ✅ **Vector Storage** - PostgreSQL + pgVector for efficient similarity search
- ✅ **Semantic Search API** - FastAPI with relevance scoring
- ✅ **Comprehensive Evaluation** - 40+ test queries across 12 due diligence categories
- 🚧 **AI Tagging** - Automated categorization (planned)

## 📊 Performance

Based on rigorous testing with 490 M&A documents and 17 critical queries:

| Metric | Performance |
|--------|-------------|
| **Top-1 Similarity** | 0.580 avg |
| **Search Speed** | ~2.1 seconds |
| **Documents Indexed** | 490 PDFs |
| **Vector Chunks** | 7,431 |
| **Query Categories** | 12 (Corporate, Legal, Financial, etc.) |

See [evaluation/CHUNKING_COMPARISON_RESULTS.md](evaluation/CHUNKING_COMPARISON_RESULTS.md) for detailed analysis.

## 🏗️ Architecture

```
┌─────────────────┐
│   PDF Input     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Extraction Layer                   │
│  ├─ PyMuPDF (primary)               │
│  └─ AWS Textract (fallback)         │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Preprocessing Layer                │
│  ├─ Text cleaning                   │
│  ├─ Header detection                │
│  └─ Section parsing                 │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Chunking Layer                     │
│  └─ Section-aware (optimized)       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Embedding Layer                    │
│  └─ HuggingFace Transformers        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Storage Layer                      │
│  └─ PostgreSQL + pgVector           │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Search API                         │
│  └─ FastAPI + Semantic Search       │
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
.
├── src/
│   ├── api/                 # FastAPI routes and endpoints ✅
│   │   └── services/        # RAG service (complete pipeline)
│   ├── chunking/            # Document chunking strategies ✅
│   ├── config/              # Configuration and settings ✅
│   ├── embeddings/          # Embedding model integrations ✅
│   ├── extraction/          # PDF text extraction ✅
│   ├── preprocessing/       # Text cleaning and parsing ✅
│   ├── search/              # Semantic search ✅
│   ├── storage/             # Database and vector store ✅
│   ├── tagging/             # Document tagging 🚧
│   └── utils/               # Utility functions ✅
├── scripts/
│   ├── init_database.py              # Database setup
│   ├── reprocess_all_documents.py    # Batch reprocessing
│   ├── evaluate_queries.py           # Search evaluation
│   ├── analyze_results.py            # Results analysis
│   └── verify_installation.py        # Installation checker
├── tests/
│   ├── unit/                # Unit tests (80+)
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test data (490 sample PDFs)
├── evaluation/              # Search quality evaluation
│   ├── ma_test_queries.json            # 40 test queries
│   ├── CHUNKING_COMPARISON_RESULTS.md  # Performance analysis
│   └── EVALUATION_GUIDE.md             # Testing methodology
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md              # System design
│   ├── CHUNKING_STRATEGIES.md       # Chunking approaches
│   ├── DATABASE_SCHEMA.md           # Database structure
│   ├── NAMING_CONVENTIONS.md        # Code standards
│   ├── UNIMPLEMENTED_FEATURES.md    # Roadmap
│   └── VECTOR_STORE_SETUP.md        # Vector DB guide
└── database/                # Database config
    └── docker-compose.yml   # PostgreSQL + pgvector

✅ = Complete | 🚧 = In Progress | ❌ = Planned
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **PostgreSQL 15+** with pgvector extension
- **Docker** (recommended for database)
- 8GB+ RAM recommended
- (Optional) AWS Account for Textract

### Installation

1. **Clone repository:**
   ```bash
   git clone <repository-url>
   cd dilligence-machines-pdf-extraction
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start database:**
   ```bash
   cd database
   docker-compose up -d
   ```

5. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults work with Docker setup)
   ```

6. **Initialize database:**
   ```bash
   python scripts/init_database.py
   ```

7. **Verify installation:**
   ```bash
   python scripts/verify_installation.py
   ```

### Quick Test

Process a sample PDF and search:

```bash
# Start API server
python run_api.py

# In another terminal, test search:
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the funding rounds?", "top_k": 5}'
```

## 💻 Usage

### Processing Documents

**Single Document:**
```python
from src.api.services.rag_service import RAGService

# Initialize service
service = RAGService()

# Process PDF
result = service.process_and_store_document("path/to/document.pdf")

print(f"Processed: {result['filename']}")
print(f"Chunks created: {len(result['chunks'])}")
```

**Batch Processing:**
```bash
python scripts/reprocess_all_documents.py
```

### Searching Documents

**Python API:**
```python
from src.api.services.rag_service import RAGService

service = RAGService()

results = service.search("What are the stock option vesting terms?", top_k=5)

for i, result in enumerate(results, 1):
    print(f"{i}. {result['filename']} (similarity: {result['score']:.3f})")
    print(f"   {result['text'][:200]}...")
```

**REST API:**
```bash
# Start server
python run_api.py

# Search
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Are there any pending lawsuits?",
    "top_k": 10,
    "min_similarity": 0.5
  }'
```

**API Response:**
```json
{
  "query": "Are there any pending lawsuits?",
  "results": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "filename": "legal-disclosures.pdf",
      "text": "...",
      "similarity_score": 0.72,
      "page_number": 5
    }
  ],
  "count": 5,
  "search_time_ms": 145
}
```

## 🔧 Configuration

Key settings in `.env`:

```bash
# Chunking Strategy (recommended: langchain)
CHUNKER_TYPE=langchain
MAX_CHUNK_SIZE=2000
CHUNK_OVERLAP=200

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pdf_rag

# Search
SEARCH_TOP_K=10
SIMILARITY_THRESHOLD=0.5
```

See [.env.example](.env.example) for full configuration options.

## 📈 Evaluation

This system includes a comprehensive evaluation framework:

### Running Evaluations

```bash
# Evaluate critical queries
python scripts/evaluate_queries.py --priority critical

# Evaluate all 40 test queries
python scripts/evaluate_queries.py --priority all

# Analyze results
python scripts/analyze_results.py evaluation/results_*.json
```

### Evaluation Categories

The system is tested against 40 queries across 12 categories:

1. Corporate Structure (3 queries)
2. Funding History (4 queries)
3. Equity & Compensation (4 queries)
4. Key Employees (3 queries)
5. Intellectual Property (3 queries)
6. Customer Contracts (4 queries)
7. Liabilities & Legal (4 queries)
8. Financial Performance (4 queries)
9. Debt & Obligations (3 queries)
10. Regulatory & Compliance (3 queries)
11. Data & Security (3 queries)
12. Governance (2 queries)

### Chunking Strategy Results

We tested three chunking strategies to optimize search quality:

| Strategy | Avg Chunk Size | Top-1 Similarity | Performance |
|----------|---------------|------------------|-------------|
| **Section-Aware** (recommended) | 215 chars | **0.580** | 🥇 Best |
| Size-Based (1000 max) | 814 chars | 0.516 | 🥈 11% worse |
| Size-Based (2000 max) | 1,482 chars | 0.508 | 🥉 12% worse |

**Key Insight:** Section-aware chunking (respecting document structure) outperforms size-based chunking because:
- Each chunk represents one coherent idea
- Embeddings focus on single topics (no signal dilution)
- 5x more "good" matches (0.6-0.8 similarity range)

See [evaluation/CHUNKING_COMPARISON_RESULTS.md](evaluation/CHUNKING_COMPARISON_RESULTS.md) for detailed analysis.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_chunker.py

# Run with coverage
pytest --cov=src tests/

# Run integration tests
pytest tests/integration/
```

## 📚 Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Chunking Strategies](docs/CHUNKING_STRATEGIES.md)** - Text segmentation approaches
- **[Database Schema](docs/DATABASE_SCHEMA.md)** - PostgreSQL + pgVector structure
- **[Evaluation Guide](evaluation/EVALUATION_GUIDE.md)** - Testing methodology
- **[Unimplemented Features](docs/UNIMPLEMENTED_FEATURES.md)** - Roadmap
- **[Contributing](CONTRIBUTING.md)** - Development guidelines

## 🛠️ Tech Stack

- **Python 3.10+** - Core language
- **FastAPI** - REST API framework
- **PostgreSQL 15+** - Relational database
- **pgVector** - Vector similarity search extension
- **HuggingFace Transformers** - Embedding models
- **PyMuPDF (fitz)** - PDF text extraction
- **LangChain** - Text chunking utilities
- **Docker** - Database containerization

## 🗺️ Roadmap

### Completed ✅
- [x] PDF text extraction with multiple strategies
- [x] Intelligent text preprocessing and cleaning
- [x] Section-aware chunking optimization
- [x] Local embedding generation
- [x] Vector storage with PostgreSQL + pgVector
- [x] Semantic search API
- [x] Comprehensive evaluation framework
- [x] 490 sample M&A documents
- [x] 40 test queries across 12 categories

### In Progress 🚧
- [ ] AI-powered document tagging
- [ ] Hybrid search (vector + keyword)
- [ ] Query result re-ranking

### Planned 📋
- [ ] AWS Bedrock integration for embeddings
- [ ] Batch processing optimization
- [ ] Web UI for document upload and search
- [ ] Advanced section parsing (numbered sections, complex headers)
- [ ] Multi-modal support (tables, images)
- [ ] Export search results to structured formats

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run evaluation to ensure quality
5. Submit pull request

## 📄 License

[MIT License](LICENSE) - See LICENSE file for details

## 🙏 Acknowledgments

- Built for M&A due diligence workflows
- Optimized through rigorous evaluation with real-world documents
- Leverages open-source tools: PostgreSQL, pgVector, HuggingFace, LangChain

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Status:** Production-ready for M&A due diligence document search
**Last Updated:** 2025-10-21
**Version:** 1.0.0
