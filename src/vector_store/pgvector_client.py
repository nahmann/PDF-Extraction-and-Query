"""
PostgreSQL + pgVector client for vector storage and similarity search.

Implements complete CRUD operations for documents and chunks with embeddings.
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from vector_store.base_store import BaseVectorStore
from vector_store.schema import Base, Document, Chunk, CREATE_EXTENSION_SQL
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PgVectorStore(BaseVectorStore):
    """Vector store using PostgreSQL + pgVector extension"""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        embedding_dim: int = 384,
        debug: bool = False
    ):
        """
        Initialize pgVector store.

        Args:
            connection_string: PostgreSQL connection string (uses settings if not provided)
            embedding_dim: Dimension of embedding vectors (must match your model)
            debug: Enable debug logging
        """
        self.connection_string = connection_string or settings.database_url
        self.embedding_dim = embedding_dim
        self.debug = debug
        self.logger = logger

        # Create engine and session
        self.engine = create_engine(
            self.connection_string,
            echo=debug,
            pool_pre_ping=True  # Verify connections before using
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

        if self.debug:
            self.logger.info(f"Initialized PgVectorStore with embedding_dim={embedding_dim}")

    def initialize_database(self):
        """
        Initialize database: create extension, tables, and indexes.

        Should be run once when setting up the database.
        """
        try:
            # Create pgvector extension
            with self.engine.connect() as conn:
                conn.execute(text(CREATE_EXTENSION_SQL))
                conn.commit()

            # Create all tables
            Base.metadata.create_all(self.engine)

            if self.debug:
                self.logger.info("Database initialized successfully")

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    def insert_document(
        self,
        filename: str,
        page_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Insert a new document record.

        Args:
            filename: Name of the PDF file
            page_count: Number of pages in document
            metadata: Additional metadata (dict)

        Returns:
            Document ID (UUID as string)
        """
        session = self.SessionLocal()
        try:
            document = Document(
                filename=filename,
                page_count=page_count,
                doc_metadata=metadata or {},
                upload_date=datetime.utcnow()
            )

            session.add(document)
            session.commit()

            doc_id = str(document.id)

            if self.debug:
                self.logger.info(f"Inserted document: {filename} (ID: {doc_id})")

            return doc_id

        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to insert document: {e}")
            raise
        finally:
            session.close()

    def insert_chunks(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Insert text chunks with embeddings for a document.

        Args:
            document_id: UUID of the parent document
            chunks: List of chunk dicts with 'text', 'embedding', 'metadata'

        Returns:
            List of chunk IDs (UUIDs as strings)
        """
        session = self.SessionLocal()
        try:
            chunk_ids = []

            for i, chunk_data in enumerate(chunks):
                chunk = Chunk(
                    document_id=uuid.UUID(document_id),
                    chunk_index=i,
                    text=chunk_data['text'],
                    embedding=chunk_data['embedding'],
                    chunk_metadata=chunk_data.get('metadata', {})
                )
                session.add(chunk)
                chunk_ids.append(str(chunk.id))

            # Update document chunk count
            document = session.query(Document).filter_by(id=uuid.UUID(document_id)).first()
            if document:
                document.chunk_count = len(chunks)
                document.updated_at = datetime.utcnow()

            session.commit()

            if self.debug:
                self.logger.info(f"Inserted {len(chunks)} chunks for document {document_id}")

            return chunk_ids

        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to insert chunks: {e}")
            raise
        finally:
            session.close()

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using cosine similarity.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional filters (e.g., {'document_id': 'uuid'})

        Returns:
            List of chunk dicts with similarity scores
        """
        session = self.SessionLocal()
        try:
            # Build base query
            query = session.query(
                Chunk,
                Chunk.embedding.cosine_distance(query_vector).label('distance')
            )

            # Apply filters
            if filters:
                if 'document_id' in filters:
                    query = query.filter(Chunk.document_id == uuid.UUID(filters['document_id']))

            # Order by similarity (lower distance = more similar)
            query = query.order_by('distance')

            # Limit results
            query = query.limit(top_k)

            # Execute query
            results = query.all()

            # Format results
            formatted_results = []
            for chunk, distance in results:
                result = chunk.to_dict(include_embedding=False)
                result['similarity'] = 1 - distance  # Convert distance to similarity score
                result['distance'] = distance
                formatted_results.append(result)

            if self.debug:
                self.logger.info(f"Search returned {len(formatted_results)} results")

            return formatted_results

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            raise
        finally:
            session.close()

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document dict or None if not found
        """
        session = self.SessionLocal()
        try:
            document = session.query(Document).filter_by(id=uuid.UUID(document_id)).first()

            if document:
                return document.to_dict()

            return None

        except Exception as e:
            self.logger.error(f"Failed to get document: {e}")
            raise
        finally:
            session.close()

    def get_document_chunks(
        self,
        document_id: str,
        include_embeddings: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document UUID
            include_embeddings: Whether to include embedding vectors

        Returns:
            List of chunk dicts
        """
        session = self.SessionLocal()
        try:
            chunks = session.query(Chunk).filter_by(
                document_id=uuid.UUID(document_id)
            ).order_by(Chunk.chunk_index).all()

            return [chunk.to_dict(include_embedding=include_embeddings) for chunk in chunks]

        except Exception as e:
            self.logger.error(f"Failed to get document chunks: {e}")
            raise
        finally:
            session.close()

    def delete_document(self, document_id: str) -> bool:
        """
        Delete document and all its chunks.

        Args:
            document_id: Document UUID

        Returns:
            True if deleted, False if not found
        """
        session = self.SessionLocal()
        try:
            document = session.query(Document).filter_by(id=uuid.UUID(document_id)).first()

            if not document:
                return False

            # Chunks will be deleted automatically due to CASCADE
            session.delete(document)
            session.commit()

            if self.debug:
                self.logger.info(f"Deleted document {document_id} and its chunks")

            return True

        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to delete document: {e}")
            raise
        finally:
            session.close()

    def delete_chunks(self, chunk_ids: List[str]) -> int:
        """
        Delete specific chunks by ID.

        Args:
            chunk_ids: List of chunk UUIDs

        Returns:
            Number of chunks deleted
        """
        session = self.SessionLocal()
        try:
            chunk_uuids = [uuid.UUID(cid) for cid in chunk_ids]

            deleted_count = session.query(Chunk).filter(
                Chunk.id.in_(chunk_uuids)
            ).delete(synchronize_session=False)

            session.commit()

            if self.debug:
                self.logger.info(f"Deleted {deleted_count} chunks")

            return deleted_count

        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to delete chunks: {e}")
            raise
        finally:
            session.close()

    def list_documents(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all documents with pagination.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List of document dicts
        """
        session = self.SessionLocal()
        try:
            documents = session.query(Document).order_by(
                Document.upload_date.desc()
            ).limit(limit).offset(offset).all()

            return [doc.to_dict() for doc in documents]

        except Exception as e:
            self.logger.error(f"Failed to list documents: {e}")
            raise
        finally:
            session.close()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dict with document count, chunk count, etc.
        """
        session = self.SessionLocal()
        try:
            document_count = session.query(Document).count()
            chunk_count = session.query(Chunk).count()

            return {
                "document_count": document_count,
                "chunk_count": chunk_count,
                "embedding_dimension": self.embedding_dim
            }

        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            if self.debug:
                self.logger.info("Database connections closed")

    # Abstract method implementations for BaseVectorStore
    def insert(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]:
        """
        Insert vectors with metadata (generic interface).

        Note: This is a simplified wrapper. For full functionality, use
        insert_document() and insert_chunks() directly.

        Args:
            vectors: List of embedding vectors
            metadata: List of metadata dicts (must include 'text' and optionally 'document_id')

        Returns:
            List of chunk IDs
        """
        raise NotImplementedError(
            "Use insert_document() and insert_chunks() for PgVectorStore. "
            "This generic insert() method is not implemented."
        )

    def delete(self, ids: List[str]) -> int:
        """
        Delete vectors by ID (generic interface).

        This wraps delete_chunks() to satisfy the base class interface.

        Args:
            ids: List of chunk UUIDs

        Returns:
            Number of items deleted
        """
        return self.delete_chunks(ids)
