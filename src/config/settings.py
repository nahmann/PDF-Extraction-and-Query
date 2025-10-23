"""
Configuration settings for the PDF processing pipeline.

Uses environment variables with sensible defaults.
"""

import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv not installed


@dataclass
class Settings:
    """Application settings with environment variable support"""

    # AWS Configuration
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_textract_max_size_mb: int = int(os.getenv("AWS_TEXTRACT_MAX_SIZE_MB", "10"))

    # Chunking Configuration
    max_chunk_size: int = int(os.getenv("MAX_CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    chunker_type: str = os.getenv("CHUNKER_TYPE", "langchain_simple")  # "langchain_simple" (recommended) or "langchain"

    # Processing Configuration
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Embedding Configuration (Part 3)
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "amazon.titan-embed-text-v1")
    # Default to 384 for sentence-transformers/all-MiniLM-L6-v2
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    embedding_normalize: bool = os.getenv("EMBEDDING_NORMALIZE", "true").lower() == "true"

    # Database Configuration (Part 4)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/pdf_rag"
    )
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"

    # Search Configuration (Part 5)
    search_top_k: int = int(os.getenv("SEARCH_TOP_K", "10"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))

    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_workers: int = int(os.getenv("API_WORKERS", "4"))

    # Storage
    upload_dir: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    temp_dir: str = os.getenv("TEMP_DIR", "./data/temp")

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables"""
        return cls()

    def validate(self) -> None:
        """Validate settings"""
        if self.max_chunk_size <= 0:
            raise ValueError("max_chunk_size must be positive")
        if self.chunk_overlap >= self.max_chunk_size:
            raise ValueError("chunk_overlap must be less than max_chunk_size")
        if self.embedding_dimension <= 0:
            raise ValueError("embedding_dimension must be positive")


# Global settings instance
settings = Settings()
