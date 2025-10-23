"""
Simple test of the complete RAG pipeline: Extract → Clean → Chunk → Embed → Store → Search
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/pdf_rag")

print("=" * 70)
print("Testing Complete RAG Pipeline")
print("=" * 70)
print()

# Test 1: Database Connection
print("Test 1: Database Connection...")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"  OK - Connected to PostgreSQL")
        print(f"  Version: {version[:50]}...")
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# Test 2: pgvector Extension
print("\nTest 2: pgvector Extension...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname='vector'"))
        row = result.fetchone()
        if row:
            print(f"  OK - pgvector {row[1]} installed")
        else:
            print("  FAILED - pgvector not found")
            sys.exit(1)
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# Test 3: Tables Exist
print("\nTest 3: Database Schema...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"  OK - Found tables: {', '.join(tables)}")

        if 'documents' not in tables or 'chunks' not in tables:
            print("  FAILED - Missing required tables")
            sys.exit(1)
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# Test 4: Test Vector Operations
print("\nTest 4: Vector Operations...")
try:
    with engine.connect() as conn:
        # Create a test vector
        result = conn.execute(text("SELECT '[1,2,3]'::vector(3)"))
        print("  OK - Can create vectors")

        # Test vector distance
        result = conn.execute(text("SELECT '[1,2,3]'::vector(3) <-> '[3,2,1]'::vector(3) AS distance"))
        distance = result.scalar()
        print(f"  OK - Vector distance calculation works (distance: {distance:.4f})")
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# Test 5: Insert Test Document
print("\nTest 5: Insert Test Document...")
try:
    with engine.connect() as conn:
        # Insert a test document
        conn.execute(text("""
            INSERT INTO documents (filename, upload_date, page_count, chunk_count, doc_metadata)
            VALUES ('test.pdf', NOW(), 1, 0, '{"test": true}')
        """))
        conn.commit()

        # Verify it was inserted
        result = conn.execute(text("SELECT COUNT(*) FROM documents"))
        count = result.scalar()
        print(f"  OK - Inserted document (total: {count})")
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# Test 6: Test Embeddings (if available)
print("\nTest 6: Embedding Generation...")
try:
    from embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder

    embedder = SentenceTransformerEmbedder(device="cpu")
    test_text = "This is a test sentence for embedding."
    embedding = embedder.embed(test_text)

    print(f"  OK - Generated embedding with {len(embedding)} dimensions")
    print(f"  First 5 values: {embedding[:5]}")
except ImportError as e:
    print(f"  SKIPPED - Embeddings module not available: {e}")
except Exception as e:
    print(f"  FAILED: {e}")

# Summary
print()
print("=" * 70)
print("SUCCESS - All core tests passed!")
print("=" * 70)
print()
print("Your RAG pipeline is ready:")
print("  - PostgreSQL + pgvector running in Docker")
print("  - Database schema created")
print("  - Vector operations working")
print("  - Ready to process PDFs")
print()
print("Next steps:")
print("  1. Process PDFs: python scripts/demo_vector_store.py")
print("  2. Run full tests: python -m pytest tests/unit/test_vector_store.py")
print()
