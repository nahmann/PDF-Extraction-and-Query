# Documentation Index

## Quick Links

- **[Main Project README](../README.md)** - Project overview and getting started
- **[Setup Complete Guide](../SETUP_COMPLETE.md)** - Current setup status and quick reference
- **[Vector Store Setup](VECTOR_STORE_SETUP.md)** - Detailed PostgreSQL + pgvector setup guide

## Documentation Files

### VECTOR_STORE_SETUP.md
Comprehensive guide for setting up PostgreSQL with pgvector extension:
- Installation instructions (Docker recommended)
- Database schema details
- Configuration options
- Troubleshooting common issues
- Performance optimization tips

## Database Setup (Quick Reference)

### Prerequisites
- Docker Desktop installed and running
- Windows virtualization enabled (Hyper-V, Virtual Machine Platform)

### Setup Steps

1. **Start Database**
   ```bash
   cd database
   docker-compose up -d
   ```

2. **Initialize Schema**
   ```bash
   python init_db_simple.py
   # Or manually:
   cat init_schema.sql | docker exec -i pdf_rag_postgres psql -U postgres -d pdf_rag
   ```

3. **Verify Setup**
   ```bash
   python test_full_pipeline.py
   ```

### Common Issues

**Port Conflict**
- Native PostgreSQL may conflict on port 5432
- Solution: Run `database/stop_native_postgres.bat` as Administrator

**Docker Not Starting**
- Ensure virtualization is enabled in BIOS/Windows Features
- Check Docker Desktop is running (whale icon in system tray)

**Connection Failed**
- Verify Docker container is running: `docker ps`
- Check DATABASE_URL in `.env` file
- Restart container: `docker-compose restart`

## Project Structure

```
docs/
├── README.md                    # This file - documentation index
└── VECTOR_STORE_SETUP.md       # Detailed vector store guide

database/
├── docker-compose.yml           # Docker configuration
├── init_db_simple.py           # Database initialization script
├── init_schema.sql             # SQL schema definition
└── stop_native_postgres.bat    # Stop conflicting PostgreSQL service

src/
├── vector_store/               # Vector storage implementation
│   ├── pgvector_client.py     # PostgreSQL + pgvector client
│   ├── schema.py              # Database models
│   ├── base_store.py          # Abstract interface
│   └── README.md              # API documentation
├── embeddings/                 # Embedding generation
├── extraction/                 # PDF text extraction
├── chunking/                   # Text chunking
├── cleaning/                   # Text cleaning
└── config/                     # Configuration

tests/
└── unit/
    └── test_vector_store.py    # Vector store tests
```

## Development Workflow

### Daily Startup
```bash
# 1. Start database
cd database
docker-compose up -d

# 2. Verify it's running
docker ps

# 3. Run your application
cd ..
python your_script.py
```

### Daily Shutdown
```bash
# Stop database (preserves data)
cd database
docker-compose down

# Or stop and remove data
docker-compose down -v
```

### Testing
```bash
# Test database connection
python test_full_pipeline.py

# Run vector store tests (requires database)
python -m pytest tests/unit/test_vector_store.py -v

# Run all tests
python -m pytest tests/
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Vector Database | PostgreSQL 16 + pgvector 0.8.1 | Store embeddings and perform similarity search |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Generate 384-dim vector embeddings |
| PDF Extraction | PyMuPDF, AWS Textract | Extract text from PDFs |
| Text Processing | LangChain | Intelligent text chunking |
| Database ORM | SQLAlchemy | Database operations |
| Container Runtime | Docker | Isolated PostgreSQL environment |

## Next Steps

Now that the infrastructure is set up:

1. **Phase 2: Semantic Search**
   - Build search engine with ranking
   - Query processing
   - Result filtering

2. **Phase 3: API Development**
   - FastAPI endpoints
   - Document upload/processing
   - Search API

3. **Phase 4: RAG Integration**
   - Claude integration
   - Context retrieval
   - Answer generation

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Docker Documentation](https://docs.docker.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Sentence Transformers](https://www.sbert.net/)

## Getting Help

If you encounter issues:

1. Check the troubleshooting section in [VECTOR_STORE_SETUP.md](VECTOR_STORE_SETUP.md)
2. Review [SETUP_COMPLETE.md](../SETUP_COMPLETE.md) for your current configuration
3. Check Docker logs: `docker logs pdf_rag_postgres`
4. Verify environment variables in `.env` file
