"""
Custom exceptions for the PDF processing pipeline.
"""


class PDFProcessingError(Exception):
    """Base exception for all PDF processing errors"""
    pass


# ============================================================================
# EXTRACTION ERRORS
# ============================================================================

class ExtractionError(PDFProcessingError):
    """Base class for extraction-related errors"""
    pass


class TextractError(ExtractionError):
    """AWS Textract specific error"""
    pass


class TextractThrottleError(TextractError):
    """Textract API rate limit exceeded"""
    pass


class PyMuPDFError(ExtractionError):
    """PyMuPDF specific error"""
    pass


class UnsupportedFileError(ExtractionError):
    """File format not supported"""
    pass


# ============================================================================
# PREPROCESSING ERRORS
# ============================================================================

class PreprocessingError(PDFProcessingError):
    """Base class for preprocessing errors"""
    pass


class TextCleaningError(PreprocessingError):
    """Error during text cleaning"""
    pass


class SectionParsingError(PreprocessingError):
    """Error during section parsing"""
    pass


# ============================================================================
# CHUNKING ERRORS
# ============================================================================

class ChunkingError(PDFProcessingError):
    """Base class for chunking errors"""
    pass


class ChunkSizeError(ChunkingError):
    """Chunk size configuration error"""
    pass


# ============================================================================
# EMBEDDING ERRORS (Part 3)
# ============================================================================

class EmbeddingError(PDFProcessingError):
    """Base class for embedding generation errors"""
    pass


class BedrockError(EmbeddingError):
    """AWS Bedrock specific error"""
    pass


# ============================================================================
# DATABASE ERRORS (Part 4)
# ============================================================================

class DatabaseError(PDFProcessingError):
    """Base class for database errors"""
    pass


class VectorStoreError(DatabaseError):
    """Vector store operation error"""
    pass


class ConnectionError(DatabaseError):
    """Database connection error"""
    pass


# ============================================================================
# SEARCH ERRORS (Part 5)
# ============================================================================

class SearchError(PDFProcessingError):
    """Base class for search errors"""
    pass


class QueryError(SearchError):
    """Query processing error"""
    pass


# ============================================================================
# VALIDATION ERRORS
# ============================================================================

class ValidationError(PDFProcessingError):
    """Input validation error"""
    pass


class FileSizeError(ValidationError):
    """File size exceeds limits"""
    pass


class FileNotFoundError(ValidationError):
    """File does not exist"""
    pass
