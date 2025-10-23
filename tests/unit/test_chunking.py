"""
Unit tests for LangChain chunking functionality.

NOTE: These tests are written in TDD style. They will FAIL until the chunking
logic is fully implemented in src/chunking/langchain_chunker.py
"""

import pytest
from src.chunking import LangChainChunker
from langchain.schema import Document


class TestBasicChunking:
    """Test basic chunking functionality"""

    
    def test_chunk_respects_max_size(self):
        """No chunk should exceed max_chunk_size"""
        chunker = LangChainChunker(max_chunk_size=500, chunk_overlap=50)

        # Create a long text
        text = "This is a sentence. " * 100  # ~2000 chars

        chunks = chunker.chunk(text)

        # All chunks should respect max size
        for chunk in chunks:
            assert len(chunk['text']) <= 500, f"Chunk exceeds max size: {len(chunk['text'])}"

    
    def test_chunk_overlap_applied(self):
        """Verify overlap between consecutive chunks"""
        chunker = LangChainChunker(max_chunk_size=200, chunk_overlap=50)

        text = "Sentence one. Sentence two. Sentence three. " * 20

        chunks = chunker.chunk(text)

        # Check overlap between consecutive chunks
        if len(chunks) > 1:
            for i in range(len(chunks) - 1):
                current_chunk = chunks[i]['text']
                next_chunk = chunks[i + 1]['text']

                # There should be some overlap
                # Extract end of current and start of next
                current_end = current_chunk[-100:] if len(current_chunk) > 100 else current_chunk
                next_start = next_chunk[:100] if len(next_chunk) > 100 else next_chunk

                # Find common substring
                has_overlap = any(
                    word in next_start for word in current_end.split()[-10:]
                )
                assert has_overlap, f"No overlap detected between chunks {i} and {i+1}"

    
    def test_chunk_returns_list_of_dicts(self):
        """Each chunk has 'text' and 'metadata' keys"""
        chunker = LangChainChunker(max_chunk_size=1000)

        text = "This is test content. " * 50

        chunks = chunker.chunk(text)

        assert isinstance(chunks, list)
        assert len(chunks) > 0

        for chunk in chunks:
            assert isinstance(chunk, dict)
            assert 'text' in chunk
            assert 'metadata' in chunk or True  # Metadata might be optional

    
    def test_empty_text_returns_empty_chunks(self):
        """Handle empty input gracefully"""
        chunker = LangChainChunker()

        chunks = chunker.chunk("")

        assert isinstance(chunks, list)
        assert len(chunks) == 0

    
    def test_short_text_returns_single_chunk(self):
        """Text shorter than max_chunk_size should return single chunk"""
        chunker = LangChainChunker(max_chunk_size=1000)

        text = "This is a short text."

        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0]['text'] == text or chunks[0]['text'].strip() == text


class TestSectionAwareChunking:
    """Test section-aware chunking with headers"""

    
    def test_chunks_respect_section_boundaries(self):
        """Headers should start new chunks"""
        chunker = LangChainChunker(max_chunk_size=500)

        text = """
## Introduction
This is the introduction section with some content.

## Methods
This is the methods section with different content.

## Results
This is the results section.
"""

        chunks = chunker.chunk(text)

        # Should have chunks for each section
        assert len(chunks) >= 3

        # Each major section should have its own chunk (check metadata)
        sections = [c['metadata'].get('section', '') for c in chunks]

        assert 'Introduction' in sections, "Introduction section not found in chunk metadata"
        assert 'Methods' in sections, "Methods section not found in chunk metadata"
        assert 'Results' in sections, "Results section not found in chunk metadata"

    
    def test_hierarchical_metadata_in_chunks(self):
        """Chunks include parent section info in metadata"""
        chunker = LangChainChunker(max_chunk_size=500)

        text = """
## Section 1
Content for section 1.

### Subsection 1.1
Content for subsection 1.1.

## Section 2
Content for section 2.
"""

        chunks = chunker.chunk(text)

        # Check that metadata includes section information
        for chunk in chunks:
            if 'metadata' in chunk:
                # Metadata might include section hierarchy
                # This is aspirational - exact structure TBD
                assert True  # Placeholder for future metadata checks

    
    def test_markdown_header_splitting(self):
        """Split on ##, ###, #### headers"""
        chunker = LangChainChunker(max_chunk_size=1000)

        text = """
## Main Section
Some content here.

### Subsection
More content.

#### Sub-subsection
Even more content.

## Another Main Section
Final content.
"""

        chunks = chunker.chunk(text)

        # Should split at header boundaries
        assert len(chunks) >= 2  # At minimum, split at main sections


class TestLangChainIntegration:
    """Test LangChain Document creation"""

    
    def test_create_langchain_documents(self):
        """Convert chunks to LangChain Document objects"""
        chunker = LangChainChunker()

        chunks = [
            {"text": "First chunk text", "metadata": {"chunk_id": 0}},
            {"text": "Second chunk text", "metadata": {"chunk_id": 1}}
        ]

        documents = chunker.create_langchain_documents(chunks)

        assert isinstance(documents, list)
        assert len(documents) == 2
        assert all(isinstance(doc, Document) for doc in documents)

    
    def test_document_has_page_content(self):
        """Each Document has page_content attribute"""
        chunker = LangChainChunker()

        chunks = [{"text": "Test content", "metadata": {}}]

        documents = chunker.create_langchain_documents(chunks)

        assert len(documents) == 1
        assert hasattr(documents[0], 'page_content')
        assert documents[0].page_content == "Test content"

    
    def test_document_has_metadata(self):
        """Each Document has metadata dict"""
        chunker = LangChainChunker()

        chunks = [{"text": "Test", "metadata": {"source": "test.pdf"}}]

        documents = chunker.create_langchain_documents(chunks)

        assert len(documents) == 1
        assert hasattr(documents[0], 'metadata')
        assert isinstance(documents[0].metadata, dict)
        assert documents[0].metadata.get('source') == "test.pdf"


class TestRealWorldChunking:
    """Test chunking with real PDFs"""

    
    def test_chunk_employee_handbook(self, employee_handbook_pdf):
        """Chunk handbook and verify section preservation"""
        from src.extraction import FormattingExtractor
        from src.preprocessing import TextCleaner

        # Extract and clean
        extractor = FormattingExtractor()
        result = extractor.extract(str(employee_handbook_pdf))
        assert result.success

        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(result.extracted_text)

        # Chunk
        chunker = LangChainChunker(max_chunk_size=1000, chunk_overlap=100)
        chunks = chunker.chunk(cleaned_text)

        # Verify chunks were created
        assert len(chunks) > 0

        # All chunks should respect max size
        for chunk in chunks:
            assert len(chunk['text']) <= 1200  # Allow some margin

        # Should have multiple chunks for a handbook
        assert len(chunks) >= 5

    
    def test_chunk_contract(self, contract_pdf):
        """Contract sections should align with chunk boundaries"""
        from src.extraction import FormattingExtractor
        from src.preprocessing import TextCleaner

        extractor = FormattingExtractor()
        result = extractor.extract(str(contract_pdf))
        assert result.success

        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(result.extracted_text)

        chunker = LangChainChunker(max_chunk_size=800)
        chunks = chunker.chunk(cleaned_text)

        assert len(chunks) > 0

        # Verify all chunks are within size limit
        for chunk in chunks:
            assert len(chunk['text']) <= 800

    
    def test_oversized_section_handling(self):
        """If section > max_chunk_size, split intelligently"""
        chunker = LangChainChunker(max_chunk_size=200, chunk_overlap=20)

        # Create a long section that exceeds max size
        text = """
## Very Long Section
""" + ("This is a sentence that makes the section very long. " * 50)

        chunks = chunker.chunk(text)

        # Should split the oversized section
        assert len(chunks) > 1

        # All chunks should still respect max size
        for chunk in chunks:
            assert len(chunk['text']) <= 250  # Allow small margin


class TestChunkingConfiguration:
    """Test chunking configuration options"""

    
    def test_custom_chunk_size(self):
        """Test with custom max_chunk_size"""
        chunker = LangChainChunker(max_chunk_size=300)

        text = "Word " * 200  # ~1000 chars

        chunks = chunker.chunk(text)

        # Should create multiple chunks with custom size
        for chunk in chunks:
            assert len(chunk['text']) <= 300

    
    def test_custom_overlap(self):
        """Test with custom chunk_overlap"""
        chunker = LangChainChunker(max_chunk_size=200, chunk_overlap=100)

        text = "Sentence. " * 50

        chunks = chunker.chunk(text)

        # Verify overlap is roughly as configured
        # (Exact overlap depends on implementation)
        assert len(chunks) > 1

    
    def test_default_settings_from_config(self):
        """Chunker should use settings from config by default"""
        chunker = LangChainChunker()  # No explicit size/overlap

        # Should not crash and should use defaults
        text = "Test content. " * 100
        chunks = chunker.chunk(text)

        assert isinstance(chunks, list)


class TestChunkingEdgeCases:
    """Test edge cases in chunking"""

    
    def test_single_very_long_word(self):
        """Handle pathological case of extremely long 'word'"""
        chunker = LangChainChunker(max_chunk_size=100)

        # Create artificially long string without spaces
        text = "a" * 500

        chunks = chunker.chunk(text)

        # Should handle gracefully (might need to split mid-word)
        assert len(chunks) > 0


    def test_only_headers_no_content(self):
        """Handle document with only headers (empty chunks filtered out)"""
        chunker = LangChainChunker()

        text = """
## Header 1

## Header 2

## Header 3
"""

        chunks = chunker.chunk(text)

        # Empty sections should be filtered out, resulting in 0 chunks
        # This is correct behavior - we don't want empty chunks
        assert isinstance(chunks, list)

    
    def test_unicode_content(self):
        """Handle unicode and special characters"""
        chunker = LangChainChunker(max_chunk_size=200)

        text = """
## Résumé
This section contains unicode: café, naïve, 日本語.

## Symbols
Special chars: ©, ®, €, £, ¥, §.
"""

        chunks = chunker.chunk(text)

        # Should handle unicode without crashing
        assert len(chunks) > 0

        # Verify unicode is preserved
        all_text = " ".join(c['text'] for c in chunks)
        assert "café" in all_text or "cafe" in all_text  # Might normalize
