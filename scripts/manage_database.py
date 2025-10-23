"""
Database Management Utility

This script helps manage the vector database:
- Clear all data (fresh start)
- Delete specific documents
- Show database statistics
- Vacuum database (reclaim space)

Usage:
    python scripts/manage_database.py --stats
    python scripts/manage_database.py --clear
    python scripts/manage_database.py --delete-document <doc_id>
    python scripts/manage_database.py --vacuum
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vector_store.pgvector_client import PgVectorStore
from config.settings import settings
from sqlalchemy import create_engine, text


class DatabaseManager:
    """Manage vector database"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.store = PgVectorStore(
            connection_string=settings.database_url,
            embedding_dim=settings.embedding_dimension,
            debug=verbose
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        docs = self.store.list_documents()

        total_chunks = sum(doc['chunk_count'] for doc in docs)

        # Get database size
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT pg_size_pretty(pg_database_size(current_database())) as size"
            ))
            db_size = result.fetchone()[0]

            # Get table sizes
            result = conn.execute(text("""
                SELECT
                    relname as table_name,
                    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
                    pg_size_pretty(pg_relation_size(relid)) as table_size,
                    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size
                FROM pg_catalog.pg_statio_user_tables
                WHERE relname IN ('documents', 'chunks')
                ORDER BY pg_total_relation_size(relid) DESC;
            """))
            table_sizes = result.fetchall()

        return {
            'document_count': len(docs),
            'chunk_count': total_chunks,
            'database_size': db_size,
            'table_sizes': table_sizes,
            'documents': docs
        }

    def display_stats(self):
        """Display database statistics"""
        stats = self.get_stats()

        print("\n" + "="*70)
        print("Database Statistics")
        print("="*70)
        print(f"\nDocuments: {stats['document_count']}")
        print(f"Chunks:    {stats['chunk_count']}")
        print(f"Database:  {stats['database_size']}")

        print("\nTable Sizes:")
        for table in stats['table_sizes']:
            table_name, total_size, table_size, index_size = table
            print(f"  {table_name:12} - Total: {total_size:>10}  Table: {table_size:>10}  Index: {index_size:>10}")

        if stats['documents']:
            print(f"\nDocuments ({len(stats['documents'])}):")
            for doc in stats['documents']:
                print(f"  • {doc['filename']} ({doc['chunk_count']} chunks)")
                print(f"    ID: {doc['id']}")
                print(f"    Uploaded: {doc['upload_date'].strftime('%Y-%m-%d %H:%M:%S')}")

    def clear_all(self, confirm: bool = False):
        """Clear all documents and chunks"""
        if not confirm:
            print("\n⚠️  WARNING: This will delete ALL documents and chunks!")

            stats = self.get_stats()
            print(f"\nThis will delete:")
            print(f"  • {stats['document_count']} document(s)")
            print(f"  • {stats['chunk_count']} chunk(s)")

            response = input("\nType 'YES' to confirm deletion: ")

            if response != 'YES':
                print("Cancelled.")
                return False

        print("\nDeleting all documents and chunks...")

        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            # Delete all chunks first (due to foreign key)
            result = conn.execute(text("DELETE FROM chunks"))
            chunks_deleted = result.rowcount

            # Delete all documents
            result = conn.execute(text("DELETE FROM documents"))
            docs_deleted = result.rowcount

            conn.commit()

        print(f"✓ Deleted {docs_deleted} document(s) and {chunks_deleted} chunk(s)")
        return True

    def delete_document(self, document_id: str):
        """Delete a specific document and its chunks"""
        # Get document info first
        doc = self.store.get_document(document_id)

        if not doc:
            print(f"\nDocument not found: {document_id}")
            return False

        print(f"\nDeleting document: {doc['filename']}")
        print(f"  Chunks: {doc['chunk_count']}")

        self.store.delete_document(document_id)

        print("✓ Deleted successfully")
        return True

    def vacuum_database(self):
        """Vacuum database to reclaim space"""
        print("\nVacuuming database (this may take a while)...")

        engine = create_engine(settings.database_url)

        # Need to use isolation level autocommit for VACUUM
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("VACUUM ANALYZE documents"))
            print("✓ Vacuumed documents table")

            conn.execute(text("VACUUM ANALYZE chunks"))
            print("✓ Vacuumed chunks table")

        print("✓ Vacuum complete")

    def cleanup(self):
        """Clean up resources"""
        self.store.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manage the vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show database statistics
  python scripts/manage_database.py --stats

  # Clear all data (fresh start)
  python scripts/manage_database.py --clear

  # Delete specific document
  python scripts/manage_database.py --delete-document abc-123-def

  # Vacuum database (reclaim space)
  python scripts/manage_database.py --vacuum

Database Management Tips:
  • Clearing database is useful when testing different chunking strategies
  • Vacuum after deleting many documents to reclaim disk space
  • Use --delete-document to remove individual documents during testing
        """
    )

    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Show database statistics'
    )

    parser.add_argument(
        '--clear', '-c',
        action='store_true',
        help='Clear all documents and chunks (requires confirmation)'
    )

    parser.add_argument(
        '--delete-document', '-d',
        type=str,
        metavar='DOC_ID',
        help='Delete a specific document by ID'
    )

    parser.add_argument(
        '--vacuum', '-v',
        action='store_true',
        help='Vacuum database to reclaim space'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompts'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )

    args = parser.parse_args()

    # If no action specified, show stats by default
    if not (args.stats or args.clear or args.delete_document or args.vacuum):
        args.stats = True

    manager = DatabaseManager(verbose=args.verbose)

    try:
        if args.stats:
            manager.display_stats()

        if args.clear:
            manager.clear_all(confirm=args.yes)

        if args.delete_document:
            manager.delete_document(args.delete_document)

        if args.vacuum:
            manager.vacuum_database()

        return 0

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        manager.cleanup()


if __name__ == "__main__":
    sys.exit(main())
