"""
List all documents in the vector database.

This script displays all uploaded documents with their metadata and statistics.
Useful for seeing what's available to query.

Usage:
    python scripts/list_documents.py
    python scripts/list_documents.py --verbose
    python scripts/list_documents.py --document-id abc-123

Requirements:
    - Database running with uploaded documents
    - DATABASE_URL configured in .env
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vector_store.pgvector_client import PgVectorStore
from config.settings import settings


def list_all_documents(verbose: bool = False) -> List[Dict[str, Any]]:
    """
    List all documents in the database.

    Args:
        verbose: Include detailed metadata

    Returns:
        List of documents with metadata
    """
    store = PgVectorStore(
        connection_string=settings.database_url,
        embedding_dim=settings.embedding_dimension,
        debug=False
    )

    try:
        documents = store.list_documents()
        return documents
    finally:
        store.close()


def get_document_details(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific document.

    Args:
        document_id: Document UUID

    Returns:
        Document details with chunks
    """
    store = PgVectorStore(
        connection_string=settings.database_url,
        embedding_dim=settings.embedding_dimension,
        debug=False
    )

    try:
        # Get document metadata
        document = store.get_document(document_id)
        if not document:
            return None

        # Get all chunks for this document
        chunks = store.get_document_chunks(document_id)
        document['chunks'] = chunks

        return document
    finally:
        store.close()


def format_document_list(documents: List[Dict[str, Any]], verbose: bool = False):
    """
    Format and print document list.

    Args:
        documents: List of documents
        verbose: Show additional details
    """
    print()
    print("=" * 70)
    print("Uploaded Documents")
    print("=" * 70)

    if not documents:
        print("\nNo documents found.")
        print("\nUpload a document:")
        print("  python scripts/upload_pdf.py document.pdf")
        return

    print(f"\nTotal: {len(documents)} document(s)\n")

    for i, doc in enumerate(documents, 1):
        doc_id = doc['id']
        filename = doc['filename']
        chunk_count = doc['chunk_count']
        page_count = doc['page_count']
        upload_date = doc['upload_date']  # Already formatted as ISO string

        print(f"{i}. {filename}")
        print(f"   Document ID: {doc_id}")
        print(f"   Uploaded: {upload_date}")
        print(f"   Pages: {page_count}")
        print(f"   Chunks: {chunk_count}")

        if verbose and doc.get('metadata'):
            print(f"   Metadata: {doc['metadata']}")

        print()


def format_document_details(document: Dict[str, Any]):
    """
    Format and print detailed document information.

    Args:
        document: Document with chunks
    """
    print()
    print("=" * 70)
    print("Document Details")
    print("=" * 70)
    print()
    print(f"Filename:     {document['filename']}")
    print(f"Document ID:  {document['id']}")
    print(f"Uploaded:     {document['upload_date']}")  # Already formatted as ISO string
    print(f"Pages:        {document['page_count']}")
    print(f"Chunks:       {document['chunk_count']}")

    if document.get('metadata'):
        print(f"Metadata:     {document['metadata']}")

    chunks = document.get('chunks', [])
    if chunks:
        print()
        print(f"Chunks ({len(chunks)}):")
        print()

        for i, chunk in enumerate(chunks, 1):
            text = chunk['text']
            chunk_index = chunk['chunk_index']
            metadata = chunk.get('metadata', {})

            # Truncate text preview
            if len(text) > 200:
                text_preview = text[:200] + "..."
            else:
                text_preview = text

            print(f"  {i}. Chunk #{chunk_index}")
            print(f"     Text: {text_preview}")

            if metadata:
                print(f"     Metadata: {metadata}")

            print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="List all documents in the vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/list_documents.py
  python scripts/list_documents.py --verbose
  python scripts/list_documents.py --document-id abc-123-def-456

Upload documents:
  python scripts/upload_pdf.py document.pdf
        """
    )

    parser.add_argument(
        '--document-id', '-d',
        type=str,
        help='Show detailed information for specific document ID'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed metadata'
    )

    args = parser.parse_args()

    try:
        if args.document_id:
            # Show details for specific document
            document = get_document_details(args.document_id)

            if not document:
                print(f"\nDocument not found: {args.document_id}", file=sys.stderr)
                print("\nList all documents:", file=sys.stderr)
                print("  python scripts/list_documents.py", file=sys.stderr)
                return 1

            format_document_details(document)

        else:
            # List all documents
            documents = list_all_documents(verbose=args.verbose)
            format_document_list(documents, verbose=args.verbose)

        return 0

    except Exception as e:
        print(f"\n Error: {e}", file=sys.stderr)
        print("\nTroubleshooting:", file=sys.stderr)
        print("  1. Is the database running?", file=sys.stderr)
        print("     Run: cd database && docker-compose up -d", file=sys.stderr)
        print("  2. Is DATABASE_URL configured in .env?", file=sys.stderr)
        print(file=sys.stderr)

        if args.verbose:
            import traceback
            traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
