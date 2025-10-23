"""
RAG Service - Business logic for document processing and search.

Reuses logic from scripts/ folder for consistency.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from vector_store.pgvector_client import PgVectorStore
from extraction.formatting_extractor import FormattingExtractor
from preprocessing.text_cleaner import TextCleaner
from chunking import create_chunker, get_chunker_info
from embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
from config.settings import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG operations - document processing and search"""

    def __init__(self):
        """Initialize RAG service with all components"""
        self.store = PgVectorStore(
            connection_string=settings.database_url,
            embedding_dim=settings.embedding_dimension,
            debug=False
        )

        self.embedder = SentenceTransformerEmbedder(
            model_name=settings.embedding_model,
            device='cpu'
        )

        self.extractor = FormattingExtractor(debug=False)
        self.cleaner = TextCleaner()
        self.chunker = create_chunker()  # Uses settings.chunker_type

        chunker_info = get_chunker_info(self.chunker)
        logger.info(
            f"RAG Service initialized with {chunker_info['type']} "
            f"(max_size={chunker_info['max_chunk_size']}, "
            f"overlap={chunker_info['chunk_overlap']})"
        )

    async def process_pdf(
        self,
        file_path: str,
        original_filename: str,
        relative_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a PDF through the full RAG pipeline.

        Reuses logic from scripts/upload_pdf.py

        Args:
            file_path: Path to the PDF file
            original_filename: Original filename
            relative_path: Optional relative path for duplicate detection

        Returns:
            Dict with document_id, filename, page_count, chunk_count, processing_time_ms
        """
        start_time = time.time()

        try:
            # 1. Extract
            logger.info(f"Extracting text from {original_filename}")
            extraction_result = self.extractor.extract(file_path)

            # 2. Clean
            logger.info(f"Cleaning text from {original_filename}")
            cleaned_text, warnings = self.cleaner.clean(extraction_result.extracted_text)

            # 3. Chunk
            logger.info(f"Chunking text from {original_filename}")
            chunks = self.chunker.chunk(cleaned_text)

            # 4. Embed
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.embed_batch(texts)

            # Add embeddings to chunks
            chunks_with_embeddings = []
            for chunk, embedding in zip(chunks, embeddings):
                chunk['embedding'] = embedding
                chunks_with_embeddings.append(chunk)

            # 5. Store
            logger.info(f"Storing document in database")
            page_count = extraction_result.metadata.get('page_count', 0)

            metadata = {
                'source_path': file_path,
                'relative_path': relative_path or original_filename,
                'extraction_method': 'FormattingExtractor',
                'cleaning_warnings': len(warnings)
            }

            document_id = self.store.insert_document(
                filename=original_filename,
                page_count=page_count,
                metadata=metadata
            )

            self.store.insert_chunks(document_id, chunks_with_embeddings)

            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Successfully processed {original_filename} ({processing_time_ms}ms)")

            return {
                'document_id': document_id,
                'filename': original_filename,
                'page_count': page_count,
                'chunk_count': len(chunks_with_embeddings),
                'processing_time_ms': processing_time_ms
            }

        except Exception as e:
            logger.error(f"Error processing {original_filename}: {e}")
            raise

    async def search_documents(
        self,
        query: str,
        top_k: int = 3,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search documents using semantic similarity.

        Reuses logic from scripts/query_documents.py

        Args:
            query: Natural language search query
            top_k: Number of results to return
            document_id: Optional filter to specific document

        Returns:
            Dict with query, results, total_results, search_time_ms
        """
        start_time = time.time()

        try:
            # Generate query embedding
            logger.info(f"Searching for: {query}")
            query_embedding = self.embedder.embed(query)

            # Build filters
            filters = {}
            if document_id:
                filters['document_id'] = document_id

            # Search vector store
            results = self.store.search(
                query_vector=query_embedding,
                top_k=top_k,
                filters=filters if filters else None
            )

            # Enrich with document details
            enriched_results = []
            for result in results:
                doc = self.store.get_document(result['document_id'])
                doc_metadata = doc.get('metadata', {})

                enriched_results.append({
                    'text': result['text'],
                    'document_name': doc['filename'],
                    'document_id': result['document_id'],
                    'relative_path': doc_metadata.get('relative_path', doc['filename']),
                    'chunk_index': result['chunk_index'],
                    'similarity': result['similarity'],
                    'metadata': result.get('metadata', {})
                })

            search_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Search completed in {search_time_ms}ms, found {len(enriched_results)} results")

            return {
                'query': query,
                'results': enriched_results,
                'total_results': len(enriched_results),
                'search_time_ms': search_time_ms
            }

        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")
            raise

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List all documents in the database.

        Reuses logic from scripts/list_documents.py

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            Dict with documents list and total count
        """
        try:
            documents = self.store.list_documents(limit=limit, offset=offset)

            # Convert to API format
            formatted_docs = []
            for doc in documents:
                formatted_docs.append({
                    'id': str(doc['id']),
                    'filename': doc['filename'],
                    'upload_date': doc['upload_date'],
                    'page_count': doc['page_count'],
                    'chunk_count': doc['chunk_count'],
                    'metadata': doc.get('metadata', {})
                })

            return {
                'documents': formatted_docs,
                'total': len(formatted_docs)
            }

        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document info or None if not found
        """
        try:
            doc = self.store.get_document(document_id)
            if not doc:
                return None

            return {
                'id': str(doc['id']),
                'filename': doc['filename'],
                'upload_date': doc['upload_date'],
                'page_count': doc['page_count'],
                'chunk_count': doc['chunk_count'],
                'metadata': doc.get('metadata', {})
            }

        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            raise

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a document and all its chunks.

        Reuses logic from scripts/manage_database.py

        Args:
            document_id: Document UUID to delete

        Returns:
            Dict with deletion status
        """
        try:
            # Get document info before deletion
            doc = self.store.get_document(document_id)
            if not doc:
                raise ValueError(f"Document not found: {document_id}")

            chunk_count = doc['chunk_count']

            # Delete document (cascades to chunks)
            self.store.delete_document(document_id)

            logger.info(f"Deleted document {document_id} and {chunk_count} chunks")

            return {
                'deleted': True,
                'document_id': document_id,
                'chunks_deleted': chunk_count
            }

        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Reuses logic from scripts/manage_database.py

        Returns:
            Dict with database stats
        """
        try:
            stats = self.store.get_stats()

            return {
                'total_documents': stats['document_count'],
                'total_chunks': stats['chunk_count'],
                'database_size': stats.get('database_size', 'unknown'),
                'avg_chunks_per_document': (
                    stats['chunk_count'] / stats['document_count']
                    if stats['document_count'] > 0 else 0
                )
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise

    def health_check(self) -> Dict[str, str]:
        """
        Check service health.

        Returns:
            Dict with component statuses
        """
        try:
            # Test database connection
            self.store.list_documents(limit=1)
            db_status = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = f"error: {str(e)}"

        return {
            'status': 'healthy' if db_status == "connected" else 'unhealthy',
            'database': db_status,
            'embedder': 'loaded'  # Embedder is loaded on init
        }

    def close(self):
        """Close database connections"""
        if self.store:
            self.store.close()


# Global service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Dependency injection for RAG service"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
