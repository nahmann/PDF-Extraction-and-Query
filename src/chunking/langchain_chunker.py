"""
LangChain-based text chunking with section awareness.

Ported from original PDF_Processor.py chunking logic.
"""

import re
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain.schema import Document

from chunking.base_chunker import BaseChunker
from config.settings import settings
from config.constants import MARKDOWN_HEADERS, CHUNK_SEPARATORS
from utils.logger import setup_logger

logger = setup_logger(__name__)


class LangChainChunker(BaseChunker):
    """Chunk text using LangChain splitters with section awareness"""

    def __init__(
        self,
        max_chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        use_section_awareness: bool = True,
        debug: bool = False
    ):
        """
        Initialize LangChain chunker.

        Args:
            max_chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
            use_section_awareness: If True, split by sections first. If False,
                                   use pure RecursiveCharacterTextSplitter (size-based)
            debug: Enable debug logging
        """
        self.max_chunk_size = max_chunk_size or settings.max_chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.use_section_awareness = use_section_awareness
        self.debug = debug
        self.logger = logger

    def chunk(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text with section awareness using LangChain.

        Process:
        1. Convert numbered sections to markdown headers
        2. Split by markdown headers (respects section boundaries)
        3. Split oversized chunks with RecursiveCharacterTextSplitter
        4. Add hierarchical metadata

        Args:
            text: Cleaned text to chunk
            metadata: Optional base metadata to add to all chunks

        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or not text.strip():
            return []

        base_metadata = metadata or {}

        # If section awareness is disabled, use simple recursive splitting
        if not self.use_section_awareness:
            if self.debug:
                self.logger.debug(f"Chunking text (section-awareness OFF): {len(text)} chars")
            return self._fallback_chunk(text, base_metadata)

        # Section-aware chunking
        # Convert to markdown headers
        markdown_text = self._convert_to_markdown(text)

        if self.debug:
            self.logger.debug(f"Chunking text (section-awareness ON): {len(text)} chars")
            self.logger.debug(f"Markdown conversion complete")

        # Define header hierarchy
        headers_to_split_on = [
            ("##", "section"),
            ("###", "subsection"),
            ("####", "subsubsection")
        ]

        # Create markdown splitter
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )

        # Split by headers
        try:
            header_chunks = markdown_splitter.split_text(markdown_text)
        except Exception as e:
            if self.debug:
                self.logger.warning(f"Markdown splitting failed: {e}, falling back to basic splitting")
            # Fallback to basic splitting if markdown splitting fails
            return self._fallback_chunk(text, base_metadata)

        # Process each chunk
        final_chunks = []

        for chunk in header_chunks:
            chunk_text = chunk.page_content
            chunk_metadata = {**base_metadata, **chunk.metadata}

            # Split oversized chunks
            if len(chunk_text) > self.max_chunk_size:
                sub_chunks = self._split_large_chunk(chunk_text, chunk_metadata)
                final_chunks.extend(sub_chunks)
            else:
                chunk_metadata["is_split_chunk"] = False
                final_chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata,
                    "chunk_size": len(chunk_text)
                })

        # Add hierarchical context
        final_chunks = self._add_section_hierarchy(final_chunks)

        if self.debug:
            self.logger.debug(f"Created {len(final_chunks)} chunks")

        return final_chunks

    def _convert_to_markdown(self, text: str) -> str:
        """
        Convert numbered sections to markdown headers.
        Only matches actual section headers, not content lines.

        Args:
            text: Text with numbered sections

        Returns:
            Text with markdown headers
        """
        lines = text.split('\n')
        output_lines = []

        for line in lines:
            # Check for sub-subsection (1.1.1)
            match = re.match(r'^(\d+\.\d+\.\d+)\.?\s+(.+)$', line)
            if match and self._is_likely_section_header(match.group(2)):
                output_lines.append(f'#### {match.group(1)} {match.group(2)}')
                continue

            # Check for subsection (1.1)
            match = re.match(r'^(\d+\.\d+)\.?\s+(.+)$', line)
            if match and self._is_likely_section_header(match.group(2)):
                output_lines.append(f'### {match.group(1)} {match.group(2)}')
                continue

            # Check for main section (1.)
            match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if match and self._is_likely_section_header(match.group(2)):
                output_lines.append(f'## {match.group(1)}. {match.group(2)}')
                continue

            # Check if line already has markdown header (from formatting extraction)
            if line.startswith('##'):
                output_lines.append(line)
                continue

            # Regular line - keep as is
            output_lines.append(line)

        return '\n'.join(output_lines)

    def _is_likely_section_header(self, text: str) -> bool:
        """
        Heuristic to determine if text is likely a section header vs content.

        A line is likely a header if:
        - Starts with capital letter
        - Is relatively short (< 100 chars)
        - Doesn't end with continuation indicators
        - Ideally title-cased

        Args:
            text: Text to check

        Returns:
            True if likely a header
        """
        text = text.strip()

        if not text:
            return False

        # Must start with capital
        if not text[0].isupper():
            return False

        # Too long to be a header
        if len(text) > 100:
            return False

        # Ends with continuation (likely incomplete sentence from content)
        if text.endswith((',', 'and', 'or', 'the', 'a', 'an', 'of', 'to', 'in')):
            return False

        # Contains common sentence continuations
        lowered = text.lower()
        if any(lowered.endswith(word) for word in ['applicable to', 'conditions', 'procedures', 'including']):
            return False

        return True

    def _split_large_chunk(
        self,
        text: str,
        base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Split a chunk that exceeds max_chunk_size using RecursiveCharacterTextSplitter.

        Args:
            text: Text to split
            base_metadata: Metadata to add to all sub-chunks

        Returns:
            List of sub-chunks
        """
        # Ensure overlap is smaller than chunk size
        overlap = min(self.chunk_overlap, self.max_chunk_size - 1)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            separators=CHUNK_SEPARATORS
        )

        sub_texts = splitter.split_text(text)
        sub_chunks = []

        for i, sub_text in enumerate(sub_texts):
            metadata = base_metadata.copy()
            metadata["chunk_part"] = f"{i+1}/{len(sub_texts)}"
            metadata["is_split_chunk"] = True

            sub_chunks.append({
                "text": sub_text,
                "metadata": metadata,
                "chunk_size": len(sub_text)
            })

        return sub_chunks

    def _add_section_hierarchy(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add hierarchical context to chunks based on section metadata.

        Args:
            chunks: List of chunks

        Returns:
            Chunks with section_hierarchy added to metadata
        """
        for chunk in chunks:
            metadata = chunk["metadata"]
            context_parts = []

            if "section" in metadata:
                context_parts.append(f"Section: {metadata['section']}")
            if "subsection" in metadata:
                context_parts.append(f"Subsection: {metadata['subsection']}")
            if "subsubsection" in metadata:
                context_parts.append(f"Sub-subsection: {metadata['subsubsection']}")

            if context_parts:
                chunk["metadata"]["section_hierarchy"] = " > ".join(context_parts)

        return chunks

    def _fallback_chunk(
        self,
        text: str,
        base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Fallback chunking method when markdown splitting fails.
        Uses simple RecursiveCharacterTextSplitter.

        Args:
            text: Text to chunk
            base_metadata: Base metadata

        Returns:
            List of chunks
        """
        if self.debug:
            self.logger.debug("Using fallback chunking method")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=CHUNK_SEPARATORS
        )

        texts = splitter.split_text(text)
        chunks = []

        for i, chunk_text in enumerate(texts):
            metadata = base_metadata.copy()
            metadata["chunk_index"] = i
            metadata["is_fallback_chunk"] = True

            chunks.append({
                "text": chunk_text,
                "metadata": metadata,
                "chunk_size": len(chunk_text)
            })

        return chunks

    def create_langchain_documents(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Document]:
        """
        Convert chunks to LangChain Document objects for vector store ingestion.

        Args:
            chunks: List of chunks from chunk()

        Returns:
            List of LangChain Document objects
        """
        documents = []
        for chunk in chunks:
            doc = Document(
                page_content=chunk["text"],
                metadata=chunk.get("metadata", {})
            )
            documents.append(doc)

        return documents
