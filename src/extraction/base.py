"""
Base extractor class for PDF text extraction.

Defines the interface that all extractors must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from utils.processing_result import ProcessingResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseExtractor(ABC):
    """Abstract base class for PDF text extractors"""

    def __init__(self, debug: bool = False):
        """
        Initialize the extractor.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug
        self.logger = setup_logger(self.__class__.__name__)

    @abstractmethod
    def extract(self, pdf_path: str) -> ProcessingResult:
        """
        Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ProcessingResult with extracted text and metadata

        Raises:
            ExtractionError: If extraction fails
        """
        pass

    @abstractmethod
    def supports_file(self, pdf_path: str) -> bool:
        """
        Check if this extractor can handle the given file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if extractor can handle this file
        """
        pass

    def _create_result(self, pdf_path: str) -> ProcessingResult:
        """
        Create a new ProcessingResult with basic metadata.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Initialized ProcessingResult
        """
        pdf_file = Path(pdf_path)
        return ProcessingResult(
            success=False,
            document_path=pdf_path,
            document_name=pdf_file.name
        )

    def _add_file_metadata(self, result: ProcessingResult) -> None:
        """
        Add file size metadata to result.

        Args:
            result: ProcessingResult to update
        """
        pdf_file = Path(result.document_path)
        if pdf_file.exists():
            file_size = pdf_file.stat().st_size
            file_size_mb = round(file_size / (1024 * 1024), 2)
            result.metadata['file_size_mb'] = file_size_mb
