"""
Input validation utilities for the PDF processing pipeline.
"""

from pathlib import Path
from typing import Optional

from utils.exceptions import ValidationError, FileSizeError, FileNotFoundError
from config.settings import settings


def validate_pdf_file(file_path: str, max_size_mb: Optional[int] = None) -> Path:
    """
    Validate that a PDF file exists and meets size requirements.

    Args:
        file_path: Path to the PDF file
        max_size_mb: Maximum file size in MB (default from settings)

    Returns:
        Validated Path object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If file is not a PDF
        FileSizeError: If file exceeds size limit
    """
    pdf_path = Path(file_path)

    # Check existence
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    # Check if it's a file (not directory)
    if not pdf_path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")

    # Check extension
    if pdf_path.suffix.lower() != '.pdf':
        raise ValidationError(f"File is not a PDF: {file_path}")

    # Check file size
    if max_size_mb is None:
        max_size_mb = 100  # Default 100MB

    file_size = pdf_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    if file_size_mb > max_size_mb:
        raise FileSizeError(
            f"File size ({file_size_mb:.2f} MB) exceeds limit ({max_size_mb} MB)"
        )

    return pdf_path


def validate_directory(directory_path: str) -> Path:
    """
    Validate that a directory exists.

    Args:
        directory_path: Path to the directory

    Returns:
        Validated Path object

    Raises:
        FileNotFoundError: If directory doesn't exist
        ValidationError: If path is not a directory
    """
    dir_path = Path(directory_path)

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    if not dir_path.is_dir():
        raise ValidationError(f"Path is not a directory: {directory_path}")

    return dir_path


def validate_chunk_config(chunk_size: int, chunk_overlap: int) -> None:
    """
    Validate chunk configuration parameters.

    Args:
        chunk_size: Maximum chunk size
        chunk_overlap: Overlap between chunks

    Raises:
        ValidationError: If configuration is invalid
    """
    if chunk_size <= 0:
        raise ValidationError(f"Chunk size must be positive: {chunk_size}")

    if chunk_overlap < 0:
        raise ValidationError(f"Chunk overlap cannot be negative: {chunk_overlap}")

    if chunk_overlap >= chunk_size:
        raise ValidationError(
            f"Chunk overlap ({chunk_overlap}) must be less than chunk size ({chunk_size})"
        )
