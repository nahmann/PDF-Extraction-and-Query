"""
Interactive RAG Pipeline Testing

This script provides a complete workflow for testing the RAG pipeline:
1. Upload all PDFs from a folder
2. Interactive query interface with detailed results
3. View full chunks and their context

Usage:
    python test_interactive_search.py
    python test_interactive_search.py --folder "path/to/pdfs"
    python test_interactive_search.py --skip-upload  # Use existing documents
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vector_store.pgvector_client import PgVectorStore
from extraction.formatting_extractor import FormattingExtractor
from preprocessing.text_cleaner import TextCleaner
from chunking.langchain_chunker import LangChainChunker
from embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
from config.settings import settings


class InteractiveTester:
    """Interactive testing interface for RAG pipeline"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.store = None
        self.embedder = None
        self.uploaded_docs = []

    def initialize(self):
        """Initialize database and embedder"""
        print("\n" + "="*70)
        print("Initializing RAG Pipeline Test Environment")
        print("="*70)

        # Initialize vector store
        print("\nConnecting to database...")
        self.store = PgVectorStore(
            connection_string=settings.database_url,
            embedding_dim=settings.embedding_dimension,
            debug=self.verbose
        )
        print("[OK] Connected")

        # Initialize embedder
        print("Loading embedding model...")
        self.embedder = SentenceTransformerEmbedder(
            model_name=settings.embedding_model,
            device='cpu'
        )
        print("[OK] Model loaded")

    def upload_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        Upload all PDFs from a folder (recursively searches subdirectories)

        Args:
            folder_path: Path to folder containing PDFs

        Returns:
            List of uploaded document info
        """
        folder = Path(folder_path)

        if not folder.exists():
            print(f"\nError: Folder not found: {folder_path}")
            return []

        # Find all PDFs recursively (including subdirectories)
        pdf_files = list(folder.rglob("*.pdf"))

        if not pdf_files:
            print(f"\nNo PDF files found in: {folder_path}")
            return []

        print(f"\n" + "="*70)
        print(f"Uploading PDFs from: {folder_path}")
        print(f"Found {len(pdf_files)} PDF file(s) (including subdirectories)")
        print("="*70)

        # Check for existing documents to avoid duplicates
        existing_docs = self.store.list_documents()
        existing_paths = {doc.get('metadata', {}).get('relative_path'): doc['id']
                         for doc in existing_docs
                         if doc.get('metadata', {}).get('relative_path')}

        uploaded = []
        skipped = []

        for i, pdf_path in enumerate(pdf_files, 1):
            # Calculate relative path from base folder
            relative_path = str(pdf_path.relative_to(folder))

            # Check if already uploaded
            if relative_path in existing_paths:
                doc_id = existing_paths[relative_path]
                skipped.append({
                    'filename': pdf_path.name,
                    'relative_path': relative_path,
                    'document_id': doc_id,
                    'reason': 'already exists'
                })
                if self.verbose:
                    print(f"\n[{i}/{len(pdf_files)}] Skipping: {relative_path} (already uploaded)")
                continue

            print(f"\n[{i}/{len(pdf_files)}] Processing: {relative_path}")
            print("-" * 70)

            try:
                result = self._process_pdf(pdf_path, folder)
                uploaded.append(result)

                print(f"[OK] Uploaded successfully")
                print(f"  Document ID: {result['document_id']}")
                print(f"  Pages: {result['page_count']}")
                print(f"  Chunks: {result['chunk_count']}")

            except Exception as e:
                print(f"[FAIL] Failed: {e}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()

        self.uploaded_docs = uploaded

        print("\n" + "="*70)
        print(f"Upload Complete: {len(uploaded)} uploaded, {len(skipped)} skipped, {len(pdf_files)} total")
        print("="*70)

        if skipped and self.verbose:
            print("\nSkipped files (already in database):")
            for item in skipped[:10]:  # Show first 10
                print(f"  - {item['relative_path']}")
            if len(skipped) > 10:
                print(f"  ... and {len(skipped) - 10} more")

        return uploaded

    def _process_pdf(self, pdf_path: Path, base_folder: Path = None) -> Dict[str, Any]:
        """
        Process a single PDF through the full pipeline

        Args:
            pdf_path: Path to the PDF file
            base_folder: Base folder for calculating relative path (optional)

        Returns:
            Dict with document_id, filename, page_count, chunk_count
        """

        # 1. Extract
        if self.verbose:
            print("  Extracting text...")
        extractor = FormattingExtractor(debug=False)
        extraction_result = extractor.extract(str(pdf_path))

        # 2. Clean
        if self.verbose:
            print("  Cleaning text...")
        cleaner = TextCleaner()
        cleaned_text, warnings = cleaner.clean(extraction_result.extracted_text)

        # 3. Chunk
        if self.verbose:
            print("  Chunking text...")
        chunker = LangChainChunker(max_chunk_size=2000, chunk_overlap=200)
        chunks = chunker.chunk(cleaned_text)

        # 4. Embed
        if self.verbose:
            print(f"  Generating embeddings for {len(chunks)} chunks...")
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedder.embed_batch(texts)

        # Add embeddings to chunks
        chunks_with_embeddings = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
            chunks_with_embeddings.append(chunk)

        # 5. Store
        if self.verbose:
            print("  Storing in database...")

        filename = pdf_path.name
        page_count = extraction_result.metadata.get('page_count', 0)

        # Calculate relative path for duplicate detection
        if base_folder:
            relative_path = str(pdf_path.relative_to(base_folder))
        else:
            relative_path = filename

        metadata = {
            'source_path': str(pdf_path),
            'relative_path': relative_path,  # Used for duplicate detection
            'extraction_method': 'FormattingExtractor',
            'cleaning_warnings': len(warnings)
        }

        document_id = self.store.insert_document(filename, page_count, metadata)
        self.store.insert_chunks(document_id, chunks_with_embeddings)

        return {
            'document_id': document_id,
            'filename': filename,
            'relative_path': relative_path,
            'page_count': page_count,
            'chunk_count': len(chunks_with_embeddings)
        }

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search all documents

        Args:
            query: Natural language query
            top_k: Number of results to return

        Returns:
            List of search results with full details
        """
        # Generate query embedding
        query_embedding = self.embedder.embed(query)

        # Search
        results = self.store.search(
            query_vector=query_embedding,
            top_k=top_k
        )

        # Enrich with document details
        for result in results:
            doc = self.store.get_document(result['document_id'])
            result['document_name'] = doc['filename']
            result['document_metadata'] = doc.get('metadata', {})

        return results

    def display_results(self, query: str, results: List[Dict[str, Any]]):
        """Display search results in a readable format"""

        print("\n" + "="*70)
        print(f"Query: {query}")
        print("="*70)

        if not results:
            print("\nNo results found.")
            return

        for i, result in enumerate(results, 1):
            similarity = result['similarity']
            doc_name = result['document_name']
            chunk_text = result['text']
            chunk_index = result['chunk_index']
            doc_id = result['document_id']
            doc_metadata = result.get('document_metadata', {})
            relative_path = doc_metadata.get('relative_path', doc_name)

            print(f"\n[Result {i}] Similarity: {similarity:.4f}")
            print(f"Document: {relative_path}")
            print(f"Chunk: #{chunk_index}")
            print(f"Document ID: {doc_id}")
            print("-" * 70)
            print(chunk_text)
            print("-" * 70)

    def interactive_query(self):
        """Interactive query loop"""

        print("\n" + "="*70)
        print("Interactive Query Mode")
        print("="*70)
        print("\nEnter queries to search documents.")
        print("Commands:")
        print("  'quit' or 'exit' - Exit the program")
        print("  'list' - Show all uploaded documents")
        print("  'top N' - Change number of results (e.g., 'top 5')")
        print("  'chunk <doc_id> <chunk_num>' - View specific chunk")
        print("\nTip: Try different phrasings of the same question to see")
        print("     how semantic search handles variations!")
        print("="*70)

        top_k = 3

        while True:
            try:
                query = input(f"\n[top {top_k}] Query: ").strip()

                if not query:
                    continue

                # Handle commands
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\nExiting...")
                    break

                elif query.lower() == 'list':
                    self._list_documents()
                    continue

                elif query.lower().startswith('top '):
                    try:
                        top_k = int(query.split()[1])
                        print(f"[OK] Now showing top {top_k} results")
                    except (IndexError, ValueError):
                        print("Usage: top N (e.g., 'top 5')")
                    continue

                elif query.lower().startswith('chunk '):
                    parts = query.split()
                    if len(parts) == 3:
                        self._view_chunk(parts[1], int(parts[2]))
                    else:
                        print("Usage: chunk <document_id> <chunk_number>")
                    continue

                # Execute search
                start_time = time.time()
                results = self.search(query, top_k=top_k)
                elapsed = time.time() - start_time

                self.display_results(query, results)
                print(f"\nSearch completed in {elapsed:.3f}s")

            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {e}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()

    def _list_documents(self):
        """List all documents in database"""
        docs = self.store.list_documents()

        print("\n" + "="*70)
        print(f"Uploaded Documents ({len(docs)})")
        print("="*70)

        for i, doc in enumerate(docs, 1):
            metadata = doc.get('metadata', {})
            relative_path = metadata.get('relative_path', doc['filename'])

            print(f"\n{i}. {relative_path}")
            print(f"   ID: {doc['id']}")
            print(f"   Chunks: {doc['chunk_count']}")
            print(f"   Uploaded: {doc['upload_date'].strftime('%Y-%m-%d %H:%M:%S')}")

    def _view_chunk(self, doc_id: str, chunk_index: int):
        """View a specific chunk"""
        try:
            chunks = self.store.get_document_chunks(doc_id)

            # Find chunk by index
            chunk = None
            for c in chunks:
                if c['chunk_index'] == chunk_index:
                    chunk = c
                    break

            if not chunk:
                print(f"Chunk #{chunk_index} not found in document {doc_id}")
                return

            doc = self.store.get_document(doc_id)

            print("\n" + "="*70)
            print(f"Chunk #{chunk_index} from {doc['filename']}")
            print("="*70)
            print(chunk['text'])
            print("="*70)
            print(f"Metadata: {chunk.get('metadata', {})}")

        except Exception as e:
            print(f"Error viewing chunk: {e}")

    def cleanup(self):
        """Clean up resources"""
        if self.store:
            self.store.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Interactive RAG pipeline testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload PDFs and start interactive query
  python test_interactive_search.py

  # Use custom folder
  python test_interactive_search.py --folder "path/to/pdfs"

  # Skip upload, use existing documents
  python test_interactive_search.py --skip-upload

  # Verbose mode
  python test_interactive_search.py --verbose

Interactive Commands:
  Query anything:     What are the stock options?
  Change results:     top 5
  List documents:     list
  View chunk:         chunk <doc_id> 0
  Exit:               quit
        """
    )

    parser.add_argument(
        '--folder', '-f',
        type=str,
        default='tests/fixtures/subset_pdfs',
        help='Folder containing PDFs to upload (default: subset_pdfs)'
    )

    parser.add_argument(
        '--skip-upload', '-s',
        action='store_true',
        help='Skip upload, use existing documents in database'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress'
    )

    args = parser.parse_args()

    tester = InteractiveTester(verbose=args.verbose)

    try:
        # Initialize
        tester.initialize()

        # Upload PDFs (unless skipped)
        if not args.skip_upload:
            uploaded = tester.upload_folder(args.folder)

            if not uploaded:
                print("\nNo documents uploaded. Exiting.")
                return 1
        else:
            print("\nSkipping upload - using existing documents in database")
            docs = tester.store.list_documents()
            print(f"Found {len(docs)} existing document(s)")

            if not docs:
                print("\nNo documents in database. Remove --skip-upload to upload PDFs.")
                return 1

        # Start interactive query loop
        tester.interactive_query()

        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())
