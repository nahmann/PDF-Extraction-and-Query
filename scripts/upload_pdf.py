"""
Upload a PDF document to the vector database.

This script processes a PDF file through the complete pipeline:
1. Extract text from PDF
2. Clean and normalize text
3. Chunk into semantic sections
4. Generate embeddings
5. Store in PostgreSQL + pgvector

Usage:
    python scripts/upload_pdf.py path/to/document.pdf
    python scripts/upload_pdf.py path/to/document.pdf --verbose

Requirements:
    - Database running: cd database && docker-compose up -d
    - DATABASE_URL configured in .env
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extraction.formatting_extractor import FormattingExtractor
from cleaning.text_cleaner import TextCleaner
from chunking.langchain_chunker import LangChainChunker
from embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
from vector_store.pgvector_client import PgVectorStore
from config.settings import settings


def process_pdf(file_path: str, verbose: bool = False) -> dict:
    """
    Process and upload a PDF to the vector database.

    Args:
        file_path: Path to PDF file
        verbose: Print detailed progress

    Returns:
        dict with document_id, filename, chunk_count, and page_count

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If processing fails
    """
    pdf_path = Path(file_path)

    # Validate file exists
    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path.absolute()}")

    if pdf_path.suffix.lower() != '.pdf':
        raise ValueError(f"Not a PDF file: {pdf_path.name}")

    if verbose:
        print(f"\nProcessing: {pdf_path.name}")
        print(f"Path: {pdf_path.absolute()}")
        print()

    # Step 1: Extract text from PDF
    if verbose:
        print("Step 1/5: Extracting text from PDF...")

    extractor = FormattingExtractor(debug=False)
    extraction_result = extractor.extract(str(pdf_path))

    if not extraction_result.success:
        raise Exception(f"Extraction failed: {extraction_result.error_message}")

    page_count = extraction_result.metadata.get('page_count', 0)
    char_count = len(extraction_result.extracted_text)

    if verbose:
        print(f"  ✓ Extracted {char_count:,} characters from {page_count} pages")

    # Step 2: Clean text
    if verbose:
        print("Step 2/5: Cleaning text...")

    cleaner = TextCleaner()
    cleaned_text, warnings = cleaner.clean(extraction_result.extracted_text)

    if verbose:
        print(f"  ✓ Cleaned text ({len(cleaned_text):,} characters)")
        if warnings:
            print(f"  Warnings: {len(warnings)}")

    # Step 3: Chunk text
    if verbose:
        print("Step 3/5: Chunking text...")

    chunker = LangChainChunker(
        max_chunk_size=settings.max_chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    chunks = chunker.chunk(cleaned_text)

    if verbose:
        print(f"  ✓ Created {len(chunks)} chunks")

    # Step 4: Generate embeddings
    if verbose:
        print(f"Step 4/5: Generating embeddings ({settings.embedding_model})...")

    embedder = SentenceTransformerEmbedder(
        model_name=settings.embedding_model,
        device="cpu",
        normalize=settings.embedding_normalize
    )

    texts = [chunk['text'] for chunk in chunks]
    embeddings = embedder.embed_batch(texts)

    if verbose:
        print(f"  ✓ Generated {len(embeddings)} embeddings ({len(embeddings[0])} dimensions)")

    # Step 5: Store in database
    if verbose:
        print("Step 5/5: Storing in database...")

    store = PgVectorStore(
        connection_string=settings.database_url,
        embedding_dim=settings.embedding_dimension,
        debug=False
    )

    try:
        # Insert document
        document_id = store.insert_document(
            filename=pdf_path.name,
            page_count=page_count,
            metadata={
                "file_size": pdf_path.stat().st_size,
                "extractor": "FormattingExtractor",
                "original_path": str(pdf_path.absolute())
            }
        )

        # Insert chunks with embeddings
        chunks_with_embeddings = [
            {
                "text": chunk['text'],
                "embedding": embedding,
                "metadata": chunk['metadata']
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

        chunk_ids = store.insert_chunks(document_id, chunks_with_embeddings)

        if verbose:
            print(f"  ✓ Uploaded to database")

        return {
            "document_id": document_id,
            "filename": pdf_path.name,
            "chunk_count": len(chunk_ids),
            "page_count": page_count
        }

    finally:
        store.close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Upload a PDF document to the vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/upload_pdf.py document.pdf
  python scripts/upload_pdf.py "path/to/my document.pdf" --verbose

After uploading, query with:
  python scripts/query_documents.py "your question here"
        """
    )

    parser.add_argument(
        'file',
        type=str,
        help='Path to PDF file to upload'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress'
    )

    args = parser.parse_args()

    try:
        # Process and upload
        result = process_pdf(args.file, verbose=args.verbose)

        # Print success message
        print()
        print("=" * 70)
        print("✓ Upload Successful")
        print("=" * 70)
        print()
        print(f"Document ID:  {result['document_id']}")
        print(f"Filename:     {result['filename']}")
        print(f"Pages:        {result['page_count']}")
        print(f"Chunks:       {result['chunk_count']}")
        print(f"Status:       Ready for search")
        print()
        print("To query this document:")
        print(f"  python scripts/query_documents.py \"your question here\"")
        print()

        return 0

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        print(f"\nMake sure the file path is correct.", file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"\n❌ Upload failed: {e}", file=sys.stderr)
        print("\nTroubleshooting:", file=sys.stderr)
        print("  1. Is the database running?", file=sys.stderr)
        print("     Run: cd database && docker-compose up -d", file=sys.stderr)
        print("  2. Is DATABASE_URL configured in .env?", file=sys.stderr)
        print("  3. Is the database initialized?", file=sys.stderr)
        print("     Run: cd database && python init_db_simple.py", file=sys.stderr)
        print(file=sys.stderr)

        if args.verbose:
            import traceback
            traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
