"""
Database initialization script for PostgreSQL + pgvector.

Run this script once to set up your vector database:
    python scripts/init_database.py

Requirements:
- PostgreSQL server running
- pgvector extension installed
- Database connection configured in .env
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vector_store.pgvector_client import PgVectorStore
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Initialize the vector database"""

    print("=" * 60)
    print("PostgreSQL + pgvector Database Initialization")
    print("=" * 60)
    print()

    # Check if database URL is configured
    if not settings.database_url or settings.database_url == "postgresql://user:password@localhost:5432/pdf_rag":
        print("ERROR: Database URL not configured!")
        print()
        print("Please set DATABASE_URL in your .env file:")
        print("  DATABASE_URL=postgresql://user:password@localhost:5432/dbname")
        print()
        print("Example:")
        print("  DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/pdf_embeddings")
        print()
        return 1

    print(f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    print()

    try:
        # Initialize vector store
        print("Connecting to database...")
        store = PgVectorStore(
            connection_string=settings.database_url,
            embedding_dim=384,  # all-MiniLM-L6-v2
            debug=True
        )

        print("Creating pgvector extension and tables...")
        store.initialize_database()

        print()
        print("=" * 60)
        print("SUCCESS! Database initialized successfully")
        print("=" * 60)
        print()
        print("Database tables created:")
        print("  - documents (stores PDF metadata)")
        print("  - chunks (stores text chunks with embeddings)")
        print()
        print("Vector index created:")
        print("  - IVFFLAT index on embeddings (cosine similarity)")
        print()
        print("You can now:")
        print("  1. Process PDFs: python scripts/demo_embeddings.py")
        print("  2. Run tests: python -m pytest tests/unit/test_vector_store.py")
        print("  3. Use the API: python -m uvicorn src.api.main:app --reload")
        print()

        # Get initial stats
        stats = store.get_stats()
        print(f"Current database stats:")
        print(f"  Documents: {stats['document_count']}")
        print(f"  Chunks: {stats['chunk_count']}")
        print(f"  Embedding dimension: {stats['embedding_dimension']}")
        print()

        store.close()
        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR: Failed to initialize database")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        print("Common issues:")
        print("  1. PostgreSQL server not running")
        print("     - Start with: sudo service postgresql start (Linux)")
        print("     - Or: brew services start postgresql (macOS)")
        print()
        print("  2. pgvector extension not installed")
        print("     - Install: https://github.com/pgvector/pgvector")
        print()
        print("  3. Database doesn't exist")
        print("     - Create: psql -U postgres -c 'CREATE DATABASE pdf_embeddings;'")
        print()
        print("  4. Wrong credentials")
        print("     - Check DATABASE_URL in .env file")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
