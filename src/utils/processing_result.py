"""
Processing result container for tracking PDF processing outcomes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ProcessingResult:
    """Container for processing results with metadata"""

    success: bool
    document_path: str
    document_name: str
    extracted_text: str = ""
    cleaned_text: str = ""
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add an error message and mark as failed"""
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message"""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "success": self.success,
            "document_path": self.document_path,
            "document_name": self.document_name,
            "extracted_text_length": len(self.extracted_text),
            "cleaned_text_length": len(self.cleaned_text),
            "chunk_count": len(self.chunks),
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata
        }

    def __repr__(self) -> str:
        """String representation"""
        status = "✓" if self.success else "✗"
        return (
            f"ProcessingResult({status} {self.document_name}: "
            f"{len(self.chunks)} chunks, {len(self.errors)} errors, "
            f"{len(self.warnings)} warnings)"
        )
