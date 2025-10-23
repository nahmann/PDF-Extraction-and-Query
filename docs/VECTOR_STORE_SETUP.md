# Vector Store Setup Guide

This guide will help you set up PostgreSQL with pgvector extension for storing and querying document embeddings.

## Prerequisites

- Python 3.8+ with pip
- PostgreSQL 12+ (14+ recommended)
- Basic command line knowledge

## Overview

The vector store uses:
- **PostgreSQL**: Robust relational database
- **pgvector**: Extension for efficient vector similarity search
- **SQLAlchemy**: ORM for database operations
- **sentence-transformers**: Local embedding generation

## Installation Steps

### 1. Install PostgreSQL

#### Windows
1. Download installer from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)
2. Run installer and follow prompts
3. Remember the password you set for the `postgres` user
4. Add PostgreSQL to PATH (usually `C:\Program Files\PostgreSQL\16\bin`)

#### macOS
```bash
# Using Homebrew
brew install postgresql@16

# Start PostgreSQL service
brew services start postgresql@16
```

#### Ubuntu/Debian
```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Install pgvector Extension

#### Windows
1. Download pgvector from [releases](https://github.com/pgvector/pgvector/releases)
2. Extract files to PostgreSQL installation directory
3. Or build from source following [pgvector Windows instructions](https://github.com/pgvector/pgvector#windows)

#### macOS
```bash
brew install pgvector
```

#### Ubuntu/Debian
```bash
# For PostgreSQL 16
sudo apt-get install postgresql-16-pgvector

# For PostgreSQL 14
sudo apt-get install postgresql-14-pgvector
```

### 3. Create Database

Open a terminal/command prompt and run:

```bash
# Connect to PostgreSQL (will prompt for password if needed)
psql -U postgres

# Create database
CREATE DATABASE pdf_rag;

# Exit psql
\q
```

Or using command line directly:
```bash
createdb -U postgres pdf_rag
```

### 4. Configure Environment

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` and update the database connection string:

```bash
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/pdf_rag
```

Connection string format:
```
postgresql://username:password@host:port/database_name
```

### 5. Initialize Database

Run the initialization script to create tables and indexes:

```bash
python scripts/init_database.py
```

You should see output like:
```
============================================================
PostgreSQL + pgvector Database Initialization
============================================================

Database URL: localhost:5432

Connecting to database...
Creating pgvector extension and tables...

============================================================
SUCCESS! Database initialized successfully
============================================================
```

### 6. Verify Installation

Check that everything is working:

```bash
# Connect to database
psql -U postgres -d pdf_rag

# Verify extension is installed
\dx

# Should see 'vector' in the list

# Verify tables exist
\dt

# Should see 'documents' and 'chunks' tables

# Exit
\q
```

## Testing the Setup

### Run Vector Store Tests

If you want to run tests (requires a test database):

```bash
# Create test database
createdb -U postgres pdf_rag_test

# Set test database URL
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/pdf_rag_test"

# Run tests
python -m pytest tests/unit/test_vector_store.py -v
```

### Process a Sample Document

Try processing one of the sample PDFs:

```bash
python scripts/demo_embeddings.py
```

This will:
1. Extract text from a PDF
2. Clean and chunk the text
3. Generate embeddings
4. Store in the database
5. Perform a sample search

## Database Schema

### Documents Table
Stores metadata about uploaded PDF files.

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
Stores text chunks with their vector embeddings.

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,  -- 384 dimensions for all-MiniLM-L6-v2
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector similarity index using IVFFLAT
CREATE INDEX ix_chunks_embedding_cosine
ON chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Document lookup index
CREATE INDEX ix_chunks_document_id ON chunks(document_id);
```

## Configuration Options

Key settings in `.env`:

```bash
# Embedding model and dimension (must match!)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Database connection
DATABASE_URL=postgresql://user:password@host:port/database
DB_POOL_SIZE=10
DB_ECHO=false  # Set to true to see SQL queries

# Search settings
SEARCH_TOP_K=10  # Default number of results
SIMILARITY_THRESHOLD=0.7  # Minimum similarity score
```

## Common Embedding Models

| Model | Dimension | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| all-MiniLM-L6-v2 | 384 | Fast | Good | General purpose (default) |
| all-mpnet-base-v2 | 768 | Slower | Better | Higher quality needed |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | Fast | Good | Multilingual documents |

**Important**: If you change the embedding model, you must:
1. Update `EMBEDDING_MODEL` in `.env`
2. Update `EMBEDDING_DIMENSION` to match the model
3. Drop and recreate the database (or recreate the chunks table with new dimension)

## Troubleshooting

### Error: "connection refused"
- PostgreSQL service is not running
- **Fix**: Start PostgreSQL service
  - Windows: Check Services panel
  - macOS: `brew services start postgresql`
  - Linux: `sudo systemctl start postgresql`

### Error: "database does not exist"
- Database hasn't been created
- **Fix**: `createdb -U postgres pdf_rag`

### Error: "extension vector does not exist"
- pgvector extension not installed
- **Fix**: Install pgvector (see step 2 above)

### Error: "authentication failed"
- Wrong username or password
- **Fix**: Update `DATABASE_URL` in `.env` with correct credentials

### Error: "permission denied to create extension"
- User doesn't have superuser privileges
- **Fix**: Connect as postgres user or grant privileges:
  ```sql
  ALTER USER your_user WITH SUPERUSER;
  ```

### Tests Failing with "Database not configured"
- `DATABASE_URL` contains placeholder values
- **Fix**: Update `.env` with real database connection string

### Slow Search Performance
- Vector index not created or not optimized
- **Fix**:
  ```sql
  -- Recreate index with more lists for larger datasets
  DROP INDEX ix_chunks_embedding_cosine;
  CREATE INDEX ix_chunks_embedding_cosine
  ON chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 1000);  -- Increase for more data

  -- Or use HNSW index (better for large datasets)
  CREATE INDEX ix_chunks_embedding_hnsw
  ON chunks USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
  ```

## Next Steps

After setting up the vector store:

1. **Process Documents**: Use the API or scripts to upload and process PDFs
2. **Implement Search**: Create search endpoints to query the vector store
3. **Integrate with Claude**: Build RAG system using search results as context
4. **Monitor Performance**: Track query times and optimize indexes as needed

## Additional Resources

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Sentence Transformers Models](https://www.sbert.net/docs/pretrained_models.html)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## Database Maintenance

### Backup Database
```bash
pg_dump -U postgres pdf_rag > backup.sql
```

### Restore Database
```bash
psql -U postgres pdf_rag < backup.sql
```

### Clear All Data
```bash
# Connect to database
psql -U postgres pdf_rag

# Delete all documents (cascades to chunks)
DELETE FROM documents;

# Or drop and recreate tables
DROP TABLE chunks;
DROP TABLE documents;
```

Then re-run `python scripts/init_database.py`

### View Statistics
```bash
# Connect to database
psql -U postgres pdf_rag

# Document count
SELECT COUNT(*) FROM documents;

# Chunk count
SELECT COUNT(*) FROM chunks;

# Storage size
SELECT pg_size_pretty(pg_database_size('pdf_rag'));

# Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public';
```
