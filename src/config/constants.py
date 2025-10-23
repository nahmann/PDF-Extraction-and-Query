"""
Constants used throughout the PDF processing pipeline.

Includes regex patterns, thresholds, and other magic numbers.
"""

import re
from typing import Tuple, List

# ============================================================================
# REGEX PATTERNS
# ============================================================================

# Section numbering patterns
PATTERN_MAIN_SECTION = re.compile(r'^(\d+)\.\s+(.+)$')
PATTERN_SUBSECTION = re.compile(r'^(\d+\.\d+)\.?\s+(.+)$')
PATTERN_SUBSUBSECTION = re.compile(r'^(\d+\.\d+\.\d+)\.?\s+(.+)$')
PATTERN_NUMBERED_LINE = re.compile(r'^\d+\.')

# Page markers
PATTERN_PAGE_MARKER = re.compile(r'-+\s*Page\s+\d+\s*-+\s*\n', flags=re.IGNORECASE)

# List patterns
PATTERN_BULLET = re.compile(r'^-\s+')
PATTERN_NUMBERED_LIST = re.compile(r'^\d+\)\s+')
PATTERN_NAME_TITLE = re.compile(r'^[A-Z][a-z]+\s+[A-Z][a-z]+,\s+')

# ============================================================================
# TEXT PROCESSING THRESHOLDS
# ============================================================================

# Header detection
MIN_HEADER_LENGTH = 15
MAX_HEADER_LENGTH = 100
SHORT_HEADER_LENGTH = 80

# Line reconstruction
MIN_LINE_LENGTH_FOR_MERGE = 15
FONT_SIZE_TOLERANCE = 1.0

# Section validation
MIN_SECTION_LENGTH = 20
MAX_SECTION_SIZE_RATIO = 10  # Largest section vs median

# ============================================================================
# SENTENCE TERMINATORS
# ============================================================================

SENTENCE_TERMINATORS: Tuple[str, ...] = ('.', ':', '!', '?', ';')

CONTINUATION_WORDS: Tuple[str, ...] = (
    'and', 'or', 'the', 'a', 'an', 'of', 'to', 'in',
    'for', 'with', 'by', 'at', 'from', 'but', 'as'
)

CONTINUATION_STARTS: Tuple[str, ...] = (
    'and ', 'or ', 'the ', 'to ', 'of ', 'in ', 'for ', 'with '
)

# ============================================================================
# FILE SIZE LIMITS
# ============================================================================

# AWS Textract limits
TEXTRACT_SYNC_MAX_SIZE_MB = 10
TEXTRACT_ASYNC_MAX_SIZE_MB = 500

# General limits
MAX_PDF_SIZE_MB = 100
MAX_PAGES = 1000

# ============================================================================
# CHUNKING SETTINGS
# ============================================================================

# LangChain separators (in order of preference)
CHUNK_SEPARATORS: List[str] = ["\n\n", "\n", ". ", " ", ""]

# Markdown headers
MARKDOWN_HEADERS: List[Tuple[str, str]] = [
    ("##", "section"),
    ("###", "subsection"),
    ("####", "subsubsection")
]

# ============================================================================
# FONT FLAGS (PyMuPDF)
# ============================================================================

# Font flags from PyMuPDF
FONT_FLAG_SUPERSCRIPT = 1
FONT_FLAG_ITALIC = 2
FONT_FLAG_SERIFED = 4
FONT_FLAG_MONOSPACED = 8
FONT_FLAG_BOLD = 16

# ============================================================================
# VALIDATION THRESHOLDS
# ============================================================================

MAX_CONTENT_LOSS_PCT = 10.0  # Maximum acceptable content loss percentage
MIN_AVERAGE_CONFIDENCE = 50.0  # Minimum OCR confidence (for Textract)

# ============================================================================
# LOGGING
# ============================================================================

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
