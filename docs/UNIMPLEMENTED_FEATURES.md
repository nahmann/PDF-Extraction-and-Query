# Unimplemented Features

This document tracks features that are planned but not yet implemented in the codebase.

## AWS Bedrock Integration

**Status:** 🚧 Planned
**Files:** `src/embeddings/bedrock_embedder.py`

### Description
Alternative embedding provider using AWS Bedrock for enterprise deployments.

### Current State
- Placeholder class exists
- Uses same interface as HuggingFaceEmbedder
- Requires boto3 and AWS credentials

### Implementation Needed
1. Add boto3 to dependencies
2. Implement Bedrock client initialization
3. Implement `embed()` method for single text
4. Implement `embed_batch()` method for multiple texts
5. Add error handling and retries
6. Add configuration for Bedrock model selection

### Priority
**Low** - HuggingFace embeddings work well for current use case

---

## AI Document Tagging

**Status:** 🚧 Planned
**Files:** `src/tagging/document_tagger.py`

### Description
Multi-stage AI workflow to automatically tag and categorize documents using Claude/Bedrock.

### Current State
- Placeholder class exists
- Interface defined but not implemented

### Implementation Needed
1. Integrate Claude API or AWS Bedrock
2. Implement document type classification (contract, financial, legal, etc.)
3. Implement metadata extraction (dates, parties, amounts)
4. Implement category tagging
5. Add confidence scores
6. Add human-in-the-loop review workflow

### Priority
**Medium** - Would improve search quality and organization

---

## Section-Based Parsing Improvements

**Status:** 🚧 Partially Implemented
**Files:**
- `src/preprocessing/section_parser.py`
- `src/preprocessing/header_detector.py`

### Description
Advanced document structure parsing beyond simple markdown headers.

### Current State
- Basic markdown header detection works (##, ###)
- Numbered sections (1., 1.1, etc.) not implemented
- Complex formatted sections not implemented
- Line reconstruction after header removal not implemented

### Implementation Needed
1. **Numbered Section Parsing:**
   - Detect patterns like "1.", "1.1", "1.1.1"
   - Handle various numbering styles (I., A., i., etc.)
   - Build hierarchical structure

2. **Formatted Sections:**
   - Detect bold/underlined headers
   - Handle all-caps headers
   - Handle centered text as headers

3. **Header Line Reconstruction:**
   - Rebuild headers that were split across lines
   - Handle multi-line titles
   - Preserve formatting

### Priority
**Low** - Current markdown-based parsing works well for test documents

---

## Batch PDF Processing

**Status:** 🚧 Planned
**Files:** `src/pipeline/orchestrator.py`

### Description
Process multiple PDFs in parallel with progress tracking and error recovery.

### Current State
- Single PDF processing works
- Batch method exists but not implemented

### Implementation Needed
1. Parallel processing using multiprocessing/threading
2. Progress bar for large batches
3. Error handling and retry logic
4. Failed document tracking and reporting
5. Resume capability for interrupted batches
6. Resource management (memory, file handles)

### Priority
**Medium** - Current single-document processing works, but batches are slow

---

## Advanced Semantic Search Features

**Status:** 🚧 Planned
**Files:** `src/search/semantic_search.py`

### Description
Enhanced search capabilities beyond basic vector similarity.

### Current State
- Basic vector similarity search works
- Placeholder for advanced features exists

### Potential Features
1. **Hybrid Search:**
   - Combine vector similarity + keyword matching
   - Re-ranking with cross-encoder models

2. **Filters:**
   - Filter by document type, date, category
   - Filter by metadata fields

3. **Query Expansion:**
   - Auto-expand queries with synonyms
   - Use LLM to rephrase queries

4. **Result Post-Processing:**
   - Combine consecutive chunks from same document
   - Deduplicate similar results
   - Highlight matching text

### Priority
**High** - Would significantly improve search quality (based on chunking analysis)

---

## File Upload API

**Status:** 🚧 Not Implemented
**Files:** `src/api/routes/upload.py`

### Description
REST API endpoint for uploading PDFs via web interface.

### Current State
- Placeholder route exists
- Returns "not implemented" error

### Implementation Needed
1. Handle multipart form data uploads
2. Validate PDF files
3. Save to data directory
4. Trigger processing pipeline
5. Return job ID for async processing
6. Add upload size limits
7. Add virus scanning (optional)

### Priority
**Low** - Command-line scripts work for current use case

---

## Recommendations

### Before Production Launch
**Must Implement:**
- ✅ Basic document processing (done)
- ✅ Vector storage and search (done)
- ✅ Chunking strategies (optimized)
- ❌ Better error handling and logging
- ❌ Database migrations/setup automation
- ❌ Health check endpoints

### Nice to Have
- AI document tagging (improves organization)
- Hybrid search with re-ranking (improves relevance)
- Batch processing optimization (faster ingestion)
- Advanced section parsing (better chunking for complex docs)

### Can Wait
- Bedrock integration (current embeddings work fine)
- Upload API (CLI works for now)
- Advanced query features (basic search is good)

---

**Last Updated:** 2025-10-21
**Maintainer:** Development Team
