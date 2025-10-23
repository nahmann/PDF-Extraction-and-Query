"""
Search uploaded documents using natural language queries.

This script searches all documents in the vector database using semantic similarity.
Returns the most relevant chunks ranked by similarity score.

Usage:
    python scripts/query_documents.py "What are the vacation policies?"
    python scripts/query_documents.py "health insurance" --top-k 5
    python scripts/query_documents.py "stock options" --document-id abc-123

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

from embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
from vector_store.pgvector_client import PgVectorStore
from config.settings import settings


def search_documents(
    query: str,
    top_k: int = 3,
    document_id: Optional[str] = None,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Search documents using semantic similarity.

    Args:
        query: Natural language search query
        top_k: Number of results to return
        document_id: Optional document ID to filter results
        verbose: Print detailed progress

    Returns:
        List of search results with similarity scores and metadata
    """
    if verbose:
        print(f"\nQuery: \"{query}\"")
        print(f"Searching for top {top_k} results...")
        print()

    # Initialize embedder
    if verbose:
        print("Loading embedding model...")

    embedder = SentenceTransformerEmbedder(
        model_name=settings.embedding_model,
        device="cpu",
        normalize=settings.embedding_normalize
    )

    # Generate query embedding
    if verbose:
        print("Generating query embedding...")

    query_embedding = embedder.embed(query)

    # Connect to database and search
    store = PgVectorStore(
        connection_string=settings.database_url,
        embedding_dim=settings.embedding_dimension,
        debug=False
    )

    try:
        # Build filters
        filters = {}
        if document_id:
            filters['document_id'] = document_id

        # Perform search
        results = store.search(
            query_vector=query_embedding,
            top_k=top_k,
            filters=filters if filters else None
        )

        # Enrich results with document names
        for result in results:
            doc = store.get_document(result['document_id'])
            if doc:
                result['document_name'] = doc['filename']
            else:
                result['document_name'] = 'Unknown'

        return results

    finally:
        store.close()


def format_results(query: str, results: List[Dict[str, Any]], verbose: bool = False):
    """
    Format and print search results.

    Args:
        query: Original query string
        results: List of search results
        verbose: Show additional details
    """
    print()
    print("=" * 70)
    print(f"Query: \"{query}\"")
    print("=" * 70)

    if not results:
        print("\nNo results found.")
        print("\nTips:")
        print("  - Try different keywords")
        print("  - Check if documents are uploaded: python scripts/list_documents.py")
        print("  - Upload documents: python scripts/upload_pdf.py file.pdf")
        return

    print(f"\nResults (top {len(results)}):\n")

    for i, result in enumerate(results, 1):
        similarity = result['similarity']
        text = result['text']
        doc_name = result.get('document_name', 'Unknown')
        metadata = result.get('metadata', {})

        # Format similarity score with color-coding (using text only, no special chars)
        if similarity >= 0.8:
            score_indicator = "[Excellent]"
        elif similarity >= 0.7:
            score_indicator = "[Good]"
        elif similarity >= 0.6:
            score_indicator = "[Fair]"
        else:
            score_indicator = "[Weak]"

        # Print result
        print(f"{i}. {score_indicator} Score: {similarity:.3f}")
        print(f"   Document: {doc_name}")

        # Truncate text to reasonable length
        if len(text) > 250:
            text_preview = text[:250] + "..."
        else:
            text_preview = text

        # Print text with indentation
        print(f"   Text: {text_preview}")

        # Print metadata if available
        if metadata and verbose:
            print(f"   Metadata: {metadata}")

        if verbose:
            print(f"   Document ID: {result['document_id']}")
            print(f"   Chunk Index: {result['chunk_index']}")

        print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Search documents using natural language queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/query_documents.py "What are the vacation policies?"
  python scripts/query_documents.py "health insurance" --top-k 5
  python scripts/query_documents.py "remote work" --verbose

Upload documents first:
  python scripts/upload_pdf.py document.pdf
        """
    )

    parser.add_argument(
        'query',
        type=str,
        help='Natural language search query'
    )

    parser.add_argument(
        '--top-k', '-k',
        type=int,
        default=3,
        help='Number of results to return (default: 3)'
    )

    parser.add_argument(
        '--document-id', '-d',
        type=str,
        help='Filter results to specific document ID'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )

    args = parser.parse_args()

    try:
        # Perform search
        results = search_documents(
            query=args.query,
            top_k=args.top_k,
            document_id=args.document_id,
            verbose=args.verbose
        )

        # Display results
        format_results(args.query, results, verbose=args.verbose)

        return 0

    except Exception as e:
        print(f"\n❌ Search failed: {e}", file=sys.stderr)
        print("\nTroubleshooting:", file=sys.stderr)
        print("  1. Is the database running?", file=sys.stderr)
        print("     Run: cd database && docker-compose up -d", file=sys.stderr)
        print("  2. Are any documents uploaded?", file=sys.stderr)
        print("     Check: python scripts/list_documents.py", file=sys.stderr)
        print("  3. Upload a document first:", file=sys.stderr)
        print("     Run: python scripts/upload_pdf.py document.pdf", file=sys.stderr)
        print(file=sys.stderr)

        if args.verbose:
            import traceback
            traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
