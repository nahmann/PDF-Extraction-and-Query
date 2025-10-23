"""
Re-process all documents with new chunking strategy.

This script:
1. Deletes all existing documents and chunks from the database
2. Re-uploads all PDFs from the data/documents directory
3. Shows progress and statistics

Usage:
    python scripts/reprocess_all_documents.py [--confirm]

    --confirm: Skip confirmation prompt (use with caution!)
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import argparse
from datetime import datetime
import time

from vector_store.pgvector_client import PgVectorStore
from extraction.formatting_extractor import FormattingExtractor
from preprocessing.text_cleaner import TextCleaner
from chunking import create_chunker, get_chunker_info
from embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


def clear_database(store: PgVectorStore) -> dict:
    """Delete all documents and chunks from database"""
    print("\nClearing database...")

    stats_before = store.get_stats()
    print(f"  Current: {stats_before['document_count']} documents, {stats_before['chunk_count']} chunks")

    # Get all documents
    docs = store.list_documents(limit=10000)

    deleted_count = 0
    for doc in docs:
        # Note: list_documents returns 'id', but delete_document expects UUID string
        store.delete_document(doc['id'])
        deleted_count += 1
        if deleted_count % 50 == 0:
            print(f"  Deleted {deleted_count} documents...")

    stats_after = store.get_stats()
    print(f"  After: {stats_after['document_count']} documents, {stats_after['chunk_count']} chunks")

    return {
        'deleted_documents': deleted_count,
        'deleted_chunks': stats_before['chunk_count']
    }


def process_all_pdfs(
    pdf_dir: Path,
    store: PgVectorStore,
    extractor,
    cleaner,
    chunker,
    embedder
) -> dict:
    """Process all PDFs in directory"""

    print(f"\nScanning for PDFs in: {pdf_dir}")
    pdf_files = list(pdf_dir.rglob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files")

    if not pdf_files:
        print("No PDF files found!")
        return {}

    chunker_info = get_chunker_info(chunker)
    print(f"\nUsing {chunker_info['type']}:")
    print(f"  Max chunk size: {chunker_info['max_chunk_size']} chars")
    print(f"  Chunk overlap: {chunker_info['chunk_overlap']} chars")

    results = {
        'total_files': len(pdf_files),
        'successful': 0,
        'failed': 0,
        'total_chunks': 0,
        'total_pages': 0,
        'errors': []
    }

    start_time = time.time()

    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            # Calculate relative path from data/documents
            try:
                relative_path = str(pdf_path.relative_to(pdf_dir))
            except ValueError:
                relative_path = pdf_path.name

            print(f"\n[{i}/{len(pdf_files)}] Processing: {relative_path}")

            # Extract
            print(f"  Extracting...")
            extraction_result = extractor.extract(str(pdf_path))

            if not extraction_result.success or not extraction_result.extracted_text:
                print(f"  [SKIP] Extraction failed: {extraction_result.errors}")
                results['failed'] += 1
                continue

            text = extraction_result.extracted_text
            page_count = extraction_result.metadata.get('page_count', 0)

            print(f"  Extracted {len(text)} chars from {page_count} pages")

            # Clean
            cleaned, warnings = cleaner.clean(text)
            print(f"  Cleaned to {len(cleaned)} chars")
            if warnings:
                print(f"  Warnings: {', '.join(warnings[:3])}")

            # Chunk
            chunks = chunker.chunk(cleaned)
            print(f"  Created {len(chunks)} chunks")

            if chunks:
                avg_chunk_size = sum(c['chunk_size'] for c in chunks) / len(chunks)
                print(f"  Avg chunk size: {avg_chunk_size:.0f} chars")

            # Embed
            print(f"  Generating embeddings...")
            texts_to_embed = [chunk['text'] for chunk in chunks]
            embeddings = embedder.embed_batch(texts_to_embed)

            # Combine
            chunks_with_embeddings = []
            for chunk, embedding in zip(chunks, embeddings):
                chunks_with_embeddings.append({
                    **chunk,
                    'embedding': embedding
                })

            # Store document (using insert_document + insert_chunks like RAG service)
            doc_metadata = {
                'relative_path': relative_path,
                'extraction_method': 'FormattingExtractor',
                'chunking_method': chunker_info['type'],
                'max_chunk_size': chunker_info['max_chunk_size'],
                'chunk_overlap': chunker_info['chunk_overlap']
            }

            doc_id = store.insert_document(
                filename=pdf_path.name,
                page_count=page_count,
                metadata=doc_metadata
            )

            store.insert_chunks(doc_id, chunks_with_embeddings)

            print(f"  [OK] Stored as {doc_id}")
            results['successful'] += 1
            results['total_chunks'] += len(chunks)
            results['total_pages'] += page_count

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            results['failed'] += 1
            results['errors'].append({
                'file': str(pdf_path),
                'error': str(e)
            })

    elapsed = time.time() - start_time
    results['elapsed_seconds'] = elapsed

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Re-process all documents with new chunking strategy"
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )
    parser.add_argument(
        '--pdf-dir',
        default='data/documents',
        help='Directory containing PDFs to process'
    )

    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir)
    if not pdf_dir.exists():
        print(f"Error: PDF directory not found: {pdf_dir}")
        return 1

    # Show current config
    print("="*80)
    print("RE-PROCESS ALL DOCUMENTS")
    print("="*80)
    print(f"\nCurrent Configuration:")
    print(f"  Chunker Type: {settings.chunker_type}")
    print(f"  Max Chunk Size: {settings.max_chunk_size} chars")
    print(f"  Chunk Overlap: {settings.chunk_overlap} chars")
    print(f"  Embedding Model: {settings.embedding_model}")
    print(f"  PDF Directory: {pdf_dir}")

    # Initialize components
    print("\nInitializing components...")
    store = PgVectorStore(
        connection_string=settings.database_url,
        embedding_dim=settings.embedding_dimension
    )

    # Get current stats
    current_stats = store.get_stats()

    # Confirmation
    if not args.confirm:
        print("\n" + "!"*80)
        print("WARNING: This will DELETE all existing documents and chunks!")
        print(f"  Current: {current_stats['document_count']} documents, {current_stats['chunk_count']} chunks")
        print("!"*80)

        response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Cancelled.")
            return 0

    # Clear database
    clear_stats = clear_database(store)

    # Initialize processing components
    print("\nInitializing processing pipeline...")
    extractor = FormattingExtractor(debug=False)
    cleaner = TextCleaner()
    chunker = create_chunker()  # Uses settings
    embedder = SentenceTransformerEmbedder(
        model_name=settings.embedding_model,
        device='cpu'
    )

    # Process all PDFs
    results = process_all_pdfs(
        pdf_dir,
        store,
        extractor,
        cleaner,
        chunker,
        embedder
    )

    # Final summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nDeleted:")
    print(f"  Documents: {clear_stats['deleted_documents']}")
    print(f"  Chunks: {clear_stats['deleted_chunks']}")

    print(f"\nProcessed:")
    print(f"  Total Files: {results['total_files']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Total Pages: {results.get('total_pages', 0)}")
    print(f"  Total Chunks: {results.get('total_chunks', 0)}")

    if results['successful'] > 0:
        print(f"  Avg Chunks/Document: {results['total_chunks'] / results['successful']:.1f}")

    print(f"\nTime Elapsed: {results.get('elapsed_seconds', 0):.1f} seconds")

    if results['failed'] > 0:
        print(f"\nErrors ({results['failed']}):")
        for error in results['errors'][:10]:  # Show first 10
            print(f"  {error['file']}: {error['error']}")

    # Verify final state
    final_stats = store.get_stats()
    print(f"\nFinal Database State:")
    print(f"  Documents: {final_stats['document_count']}")
    print(f"  Chunks: {final_stats['chunk_count']}")
    print(f"  Avg Chunks/Doc: {final_stats['chunk_count'] / final_stats['document_count']:.1f}" if final_stats['document_count'] > 0 else "  N/A")

    print("\n" + "="*80)
    print("[DONE] Re-processing complete!")
    print("="*80)
    print("\nNext steps:")
    print("1. Restart the API server: python run_api.py")
    print("2. Re-run evaluation: python scripts/evaluate_queries.py --priority critical")
    print("3. Compare results to previous run")

    return 0


if __name__ == "__main__":
    sys.exit(main())
