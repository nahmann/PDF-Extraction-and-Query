"""
Database schema definitions for PostgreSQL + pgvector.

SQLAlchemy models for documents and chunks with vector embeddings.
"""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Document(Base):
    """
    Document table - stores PDF metadata.

    Each document represents one uploaded PDF file.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    page_count = Column(Integer)
    chunk_count = Column(Integer, default=0)
    doc_metadata = Column(JSONB, default=dict)  # renamed from 'metadata' (SQLAlchemy reserved)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to chunks
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', chunks={self.chunk_count})>"

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "id": str(self.id),
            "filename": self.filename,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "metadata": self.doc_metadata,  # expose as 'metadata' in API
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Chunk(Base):
    """
    Chunk table - stores text chunks with vector embeddings.

    Each chunk is a section of text from a document with its embedding vector.
    """
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)  # 384 for all-MiniLM-L6-v2
    chunk_metadata = Column(JSONB, default=dict)  # renamed from 'metadata' (SQLAlchemy reserved)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to document
    document = relationship("Document", back_populates="chunks")

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_chunks_document_id", "document_id"),
        Index("ix_chunks_embedding_cosine", "embedding", postgresql_using="ivfflat", postgresql_ops={"embedding": "vector_cosine_ops"}),
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"

    def to_dict(self, include_embedding=False):
        """Convert to dictionary for serialization"""
        result = {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "chunk_index": self.chunk_index,
            "text": self.text,
            "metadata": self.chunk_metadata,  # expose as 'metadata' in API
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

        if include_embedding:
            result["embedding"] = self.embedding

        return result


# SQL for creating the vector extension (run this first)
CREATE_EXTENSION_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;
"""

# SQL for creating indexes (if not created automatically)
CREATE_INDEXES_SQL = """
-- Index for document lookups
CREATE INDEX IF NOT EXISTS ix_chunks_document_id ON chunks(document_id);

-- Vector similarity index (IVFFLAT)
-- Note: This requires data to be present first, or use HNSW instead
CREATE INDEX IF NOT EXISTS ix_chunks_embedding_cosine
ON chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Alternative: HNSW index (better for larger datasets, no training needed)
-- CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
-- ON chunks USING hnsw (embedding vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);
"""
