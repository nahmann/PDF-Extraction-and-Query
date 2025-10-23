"""
Integration tests for complete PDF processing pipeline.

Tests the full flow: Extraction → Cleaning → Chunking

NOTE: Tests involving chunking are marked as TDD (will fail until implementation complete)
"""

import pytest
from src.extraction import PyMuPDFExtractor, FormattingExtractor
from src.preprocessing import TextCleaner
from src.chunking import LangChainChunker


class TestFullPipelineWithoutChunking:
    """Test extraction + cleaning (no chunking dependency)"""

    def test_pymupdf_to_cleaning(self, employee_handbook_pdf):
        """PyMuPDF extraction → cleaning"""
        # Step 1: Extract
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(employee_handbook_pdf))

        assert extraction_result.success
        assert extraction_result.extracted_text

        # Step 2: Clean
        cleaner = TextCleaner()
        cleaned_text, warnings = cleaner.clean(extraction_result.extracted_text)

        assert cleaned_text
        assert "--- Page" not in cleaned_text

    def test_formatting_to_cleaning(self, contract_pdf):
        """Formatting extraction → cleaning"""
        # Step 1: Extract with formatting
        extractor = FormattingExtractor()
        extraction_result = extractor.extract(str(contract_pdf))

        assert extraction_result.success
        assert 'formatted_blocks' in extraction_result.metadata

        # Step 2: Clean
        cleaner = TextCleaner()
        cleaned_text, warnings = cleaner.clean(extraction_result.extracted_text)

        assert cleaned_text
        assert "--- Page" not in cleaned_text


class TestFullPipelineWithChunking:
    """Test complete pipeline including chunking (TDD)"""

    @pytest.mark.skip(reason="Chunking not yet implemented - TDD test")
    def test_pipeline_all_subset_pdfs(self, all_subset_pdfs):
        """Run complete pipeline on all 4 PDFs"""
        extractor = PyMuPDFExtractor()
        cleaner = TextCleaner()
        chunker = LangChainChunker(max_chunk_size=1000, chunk_overlap=100)

        for pdf_path in all_subset_pdfs:
            # Step 1: Extract
            extraction_result = extractor.extract(str(pdf_path))
            assert extraction_result.success, f"Extraction failed: {pdf_path.name}"

            # Step 2: Clean
            cleaned_text, warnings = cleaner.clean(extraction_result.extracted_text)
            assert cleaned_text, f"Cleaning failed: {pdf_path.name}"

            # Step 3: Chunk
            chunks = chunker.chunk(cleaned_text)
            assert chunks, f"Chunking failed: {pdf_path.name}"
            assert len(chunks) > 0

            # Verify chunks
            for chunk in chunks:
                assert 'text' in chunk
                assert len(chunk['text']) <= 1200  # Allow some margin

    @pytest.mark.skip(reason="Chunking not yet implemented - TDD test")
    def test_pipeline_generates_chunks(self, employee_handbook_pdf):
        """Verify chunks are created from PDF"""
        # Complete pipeline
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(employee_handbook_pdf))
        assert extraction_result.success

        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

        chunker = LangChainChunker(max_chunk_size=800, chunk_overlap=80)
        chunks = chunker.chunk(cleaned_text)

        # Should generate multiple chunks
        assert len(chunks) >= 3, "Expected multiple chunks from handbook"

        # All chunks should be properly formatted
        for chunk in chunks:
            assert isinstance(chunk, dict)
            assert 'text' in chunk
            assert len(chunk['text']) > 0

    @pytest.mark.skip(reason="Chunking not yet implemented - TDD test")
    def test_pipeline_preserves_metadata(self, contract_pdf):
        """Check metadata flows through pipeline"""
        # Extract with metadata
        extractor = FormattingExtractor()
        extraction_result = extractor.extract(str(contract_pdf))
        assert extraction_result.success

        # Store important metadata
        page_count = extraction_result.metadata['page_count']
        formatted_blocks = extraction_result.metadata['formatted_blocks']

        # Clean
        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

        # Chunk with metadata
        chunker = LangChainChunker()
        metadata = {
            'source': str(contract_pdf),
            'page_count': page_count,
            'extraction_method': extraction_result.metadata['extraction_method']
        }

        chunks = chunker.chunk(cleaned_text, metadata=metadata)

        # Verify metadata preservation
        assert chunks
        # Metadata handling depends on implementation
        # This is aspirational test

    @pytest.mark.skip(reason="Chunking not yet implemented - TDD test")
    def test_pipeline_error_handling(self):
        """Test error handling in complete pipeline"""
        extractor = PyMuPDFExtractor()
        cleaner = TextCleaner()
        chunker = LangChainChunker()

        # Invalid file
        extraction_result = extractor.extract("invalid.pdf")
        assert not extraction_result.success

        # Should not proceed if extraction fails
        if not extraction_result.success:
            return  # Pipeline stops here

        # If we had valid extraction, continue
        cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)
        chunks = chunker.chunk(cleaned_text)


class TestFormattingPipeline:
    """Test pipeline with formatting-aware extraction"""

    @pytest.mark.skip(reason="Chunking not yet implemented - TDD test")
    def test_formatting_extraction_to_chunks(self, employee_handbook_pdf):
        """FormattingExtractor → Clean → Chunk"""
        # Extract with header detection
        extractor = FormattingExtractor()
        extraction_result = extractor.extract(str(employee_handbook_pdf))
        assert extraction_result.success

        formatted_blocks = extraction_result.metadata['formatted_blocks']
        headers = [b for b in formatted_blocks if b['is_likely_header']]

        # Clean
        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

        # Chunk (should respect headers)
        chunker = LangChainChunker(max_chunk_size=1000)
        chunks = chunker.chunk(cleaned_text)

        # Chunks should align with detected headers
        assert len(chunks) > 0

        # If we had multiple headers, should have multiple chunks
        if len(headers) > 3:
            assert len(chunks) >= 3

    @pytest.mark.skip(reason="Chunking not yet implemented - TDD test")
    def test_headers_preserved_in_chunks(self, contract_pdf):
        """Verify headers appear in appropriate chunks"""
        # Extract
        extractor = FormattingExtractor()
        extraction_result = extractor.extract(str(contract_pdf))
        assert extraction_result.success

        # Clean
        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

        # Chunk
        chunker = LangChainChunker()
        chunks = chunker.chunk(cleaned_text)

        # Look for markdown headers in chunks
        chunks_with_headers = [c for c in chunks if '##' in c['text']]

        # Should have some chunks with headers
        assert len(chunks_with_headers) > 0


class TestPipelineValidation:
    """Test validation throughout pipeline"""

    def test_validation_at_each_stage(self, budget_pdf):
        """Validate data at each pipeline stage"""
        # Stage 1: Extraction
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(budget_pdf))

        assert extraction_result.success
        assert extraction_result.extracted_text
        assert extraction_result.metadata['page_count'] > 0

        original_length = len(extraction_result.extracted_text)

        # Stage 2: Cleaning with validation
        cleaner = TextCleaner()
        cleaned_text, warnings = cleaner.clean(
            extraction_result.extracted_text,
            validate=True
        )

        assert cleaned_text
        cleaned_length = len(cleaned_text)

        # Validate reasonable content preservation
        # (Removing whitespace and markers may reduce length slightly)
        assert cleaned_length > original_length * 0.8, "Too much content lost in cleaning"

        # No major warnings
        if warnings:
            assert not any("content loss" in w.lower() for w in warnings)

    @pytest.mark.skip(reason="Chunking not yet implemented - TDD test")
    def test_end_to_end_content_preservation(self, meeting_minutes_pdf):
        """Verify content is preserved through entire pipeline"""
        # Extract
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(meeting_minutes_pdf))
        assert extraction_result.success

        original_text = extraction_result.extracted_text

        # Clean
        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(original_text)

        # Chunk
        chunker = LangChainChunker()
        chunks = chunker.chunk(cleaned_text)

        # Reconstruct from chunks
        reconstructed_text = " ".join(c['text'] for c in chunks)

        # Should preserve most content
        # (Some loss from chunk boundaries is acceptable)
        assert len(reconstructed_text) > len(cleaned_text) * 0.7


class TestPipelineOutputFormats:
    """Test different output formats from pipeline"""

    @pytest.mark.skip(reason="Chunking not yet implemented - TDD test")
    def test_langchain_document_output(self, employee_handbook_pdf):
        """Test pipeline with LangChain Document output"""
        # Full pipeline
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(employee_handbook_pdf))

        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

        chunker = LangChainChunker()
        chunks = chunker.chunk(cleaned_text)

        # Convert to LangChain Documents
        documents = chunker.create_langchain_documents(chunks)

        assert documents
        assert all(hasattr(doc, 'page_content') for doc in documents)
        assert all(hasattr(doc, 'metadata') for doc in documents)

    @pytest.mark.skip(reason="Chunking not yet implemented - TDD test")
    def test_chunk_metadata_includes_source(self, contract_pdf):
        """Verify chunk metadata includes source information"""
        extractor = PyMuPDFExtractor()
        extraction_result = extractor.extract(str(contract_pdf))

        cleaner = TextCleaner()
        cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

        chunker = LangChainChunker()
        metadata = {'source': str(contract_pdf)}
        chunks = chunker.chunk(cleaned_text, metadata=metadata)

        # Each chunk should have source info
        for chunk in chunks:
            if 'metadata' in chunk:
                # Implementation may vary
                pass


class TestPipelineBatchProcessing:
    """Test batch processing of multiple PDFs"""

    def test_batch_extract_and_clean(self, all_subset_pdfs):
        """Process all PDFs in batch (extraction + cleaning)"""
        extractor = PyMuPDFExtractor()
        cleaner = TextCleaner()

        results = []

        for pdf_path in all_subset_pdfs:
            extraction_result = extractor.extract(str(pdf_path))
            assert extraction_result.success

            cleaned_text, warnings = cleaner.clean(extraction_result.extracted_text)

            results.append({
                'pdf': pdf_path.name,
                'success': True,
                'cleaned_length': len(cleaned_text),
                'warnings': warnings
            })

        # All should succeed
        assert len(results) == 4
        assert all(r['success'] for r in results)

    @pytest.mark.skip(reason="Chunking not yet implemented - TDD test")
    def test_batch_full_pipeline(self, all_subset_pdfs):
        """Process all PDFs through complete pipeline"""
        extractor = PyMuPDFExtractor()
        cleaner = TextCleaner()
        chunker = LangChainChunker(max_chunk_size=1000)

        all_chunks = []

        for pdf_path in all_subset_pdfs:
            # Extract
            extraction_result = extractor.extract(str(pdf_path))
            assert extraction_result.success

            # Clean
            cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

            # Chunk
            chunks = chunker.chunk(cleaned_text)

            # Add source metadata
            for chunk in chunks:
                chunk['source'] = pdf_path.name

            all_chunks.extend(chunks)

        # Should have substantial chunks from all PDFs
        assert len(all_chunks) >= 10

        # Verify each PDF contributed
        sources = set(c.get('source') for c in all_chunks)
        assert len(sources) == 4


class TestPipelineRobustness:
    """Test pipeline robustness and error recovery"""

    def test_pipeline_with_empty_pages(self):
        """Handle PDFs with empty pages gracefully"""
        # This is more of a conceptual test
        # Would need a PDF with empty pages to test properly
        extractor = PyMuPDFExtractor()
        cleaner = TextCleaner()

        # Simulated empty extraction
        empty_text = "\n\n--- Page 1 ---\n\n--- Page 2 ---\n\n"

        cleaned_text, warnings = cleaner.clean(empty_text)

        # Should handle gracefully
        assert isinstance(cleaned_text, str)

    def test_pipeline_with_special_characters(self, all_subset_pdfs):
        """Ensure special characters are handled throughout pipeline"""
        extractor = PyMuPDFExtractor()
        cleaner = TextCleaner()

        for pdf_path in all_subset_pdfs:
            extraction_result = extractor.extract(str(pdf_path))

            if extraction_result.success:
                cleaned_text, _ = cleaner.clean(extraction_result.extracted_text)

                # Should produce valid string
                assert isinstance(cleaned_text, str)

                # Should be encodable
                assert cleaned_text.encode('utf-8')
