# Scripts Reference Guide

This document categorizes all scripts by their purpose and necessity.

## 🟢 Essential Scripts (Keep - Used Regularly)

### 1. `init_database.py` ⭐
**Purpose:** Initialize PostgreSQL + pgvector database schema
**Used for:** First-time setup, database reset
**Frequency:** Once on initial setup, occasionally for resets
**Keep:** ✅ **ESSENTIAL**

```bash
python scripts/init_database.py
```

**Why essential:**
- Required for first-time GitHub users
- Creates tables, extensions, indexes
- Validates database connection

---

### 2. `evaluate_queries.py` ⭐
**Purpose:** Run evaluation framework with 40 test queries
**Used for:** Testing search quality, chunking optimization
**Frequency:** Regular (after changes to chunking/embeddings)
**Keep:** ✅ **ESSENTIAL**

```bash
python scripts/evaluate_queries.py --priority critical
python scripts/evaluate_queries.py --priority all
```

**Why essential:**
- Core evaluation framework
- Used for chunking comparison
- Quality assurance testing

---

### 3. `analyze_results.py` ⭐
**Purpose:** Analyze evaluation results, generate reports
**Used for:** Understanding search performance
**Frequency:** After each evaluation run
**Keep:** ✅ **ESSENTIAL**

```bash
python scripts/analyze_results.py evaluation/results_*.json
```

**Why essential:**
- Provides similarity score analysis
- Identifies low-performing queries
- Generates actionable insights

---

### 4. `reprocess_all_documents.py` ⭐
**Purpose:** Batch reprocess all PDFs with new chunking strategy
**Used for:** Testing chunking changes, rebuilding index
**Frequency:** When changing chunking strategy
**Keep:** ✅ **ESSENTIAL**

```bash
python scripts/reprocess_all_documents.py
```

**Why essential:**
- Used for chunking optimization tests
- Bulk document processing
- Index rebuilding

---

### 5. `verify_installation.py` ⭐
**Purpose:** Verify system setup (dependencies, database, etc.)
**Used for:** Troubleshooting, first-time setup validation
**Frequency:** Once on setup, when debugging issues
**Keep:** ✅ **ESSENTIAL**

```bash
python scripts/verify_installation.py
```

**Why essential:**
- Helps new users validate setup
- Debugging tool
- Checks all dependencies

---

## 🟡 Useful Utility Scripts (Keep - Occasionally Used)

### 6. `query_documents.py`
**Purpose:** Interactive CLI for searching documents
**Used for:** Manual testing, quick searches
**Frequency:** Occasional
**Keep:** ✅ **USEFUL**

```bash
python scripts/query_documents.py
```

**Why useful:**
- Quick manual testing
- Demo purposes
- Alternative to API

---

### 7. `list_documents.py`
**Purpose:** List all documents in database with stats
**Used for:** Checking what's indexed, database inspection
**Frequency:** Occasional
**Keep:** ✅ **USEFUL**

```bash
python scripts/list_documents.py
```

**Why useful:**
- Database inspection
- Verify document count
- Check metadata

---

### 8. `manage_database.py`
**Purpose:** Database management (clear, stats, etc.)
**Used for:** Database maintenance
**Frequency:** Occasional
**Keep:** ✅ **USEFUL**

```bash
python scripts/manage_database.py
```

**Why useful:**
- Clear database
- Get statistics
- Maintenance tasks

---

### 9. `upload_pdf.py`
**Purpose:** Upload single PDF via CLI
**Used for:** Quick single document testing
**Frequency:** Occasional
**Keep:** ✅ **USEFUL**

```bash
python scripts/upload_pdf.py path/to/document.pdf
```

**Why useful:**
- Single document processing
- Quick testing
- Alternative to batch processing

---

## 🔴 Demo/Example Scripts (Optional - Consider Removing)

### 10. `demo_embeddings.py`
**Purpose:** Demonstrate Extract → Clean → Chunk → Embed pipeline
**Used for:** Learning, documentation examples
**Frequency:** Rarely (mostly for new developers)
**Keep:** ⚠️ **OPTIONAL**

**Recommendation:** Move to `examples/` directory or remove

**Reasoning:**
- Redundant with `demo_vector_store.py`
- Not used in testing
- Educational only
- Can be recreated from documentation

---

### 11. `demo_vector_store.py`
**Purpose:** End-to-end demo of RAG pipeline
**Used for:** Learning, documentation examples
**Frequency:** Rarely
**Keep:** ⚠️ **OPTIONAL**

**Recommendation:** Keep ONE demo script, remove the other

**Reasoning:**
- Overlaps with `demo_embeddings.py`
- Not used in regular workflow
- Can be replaced by documentation examples
- Consider keeping as single `examples/demo.py`

---

## 📊 Summary by Use Case

### First-Time GitHub User Setup
**Required scripts:**
1. ✅ `init_database.py` - Create database schema
2. ✅ `verify_installation.py` - Validate setup
3. ✅ `reprocess_all_documents.py` - Index documents (optional, depends on if PDFs included)

**Docker covers:**
- PostgreSQL installation
- pgvector extension
- Database server startup

**Scripts still needed:**
- Schema creation (`init_database.py`)
- Validation (`verify_installation.py`)

---

### Regular Testing Workflow
**Used regularly:**
1. ✅ `evaluate_queries.py` - Run evaluation
2. ✅ `analyze_results.py` - Analyze results
3. ✅ `reprocess_all_documents.py` - Rebuild with new chunking
4. ✅ `query_documents.py` - Manual testing

---

### Occasional Maintenance
**Used occasionally:**
1. ✅ `list_documents.py` - Check indexed docs
2. ✅ `manage_database.py` - Database maintenance
3. ✅ `upload_pdf.py` - Single doc upload

---

## 🎯 Recommendations

### Keep (11 scripts → 9 scripts)

**Essential (5):**
- `init_database.py`
- `evaluate_queries.py`
- `analyze_results.py`
- `reprocess_all_documents.py`
- `verify_installation.py`

**Useful (4):**
- `query_documents.py`
- `list_documents.py`
- `manage_database.py`
- `upload_pdf.py`

### Remove or Move (2)

**Option 1: Remove completely**
- `demo_embeddings.py` - Redundant with documentation
- `demo_vector_store.py` - Redundant with documentation

**Option 2: Consolidate**
- Create `examples/` directory
- Merge both into single `examples/demo_pipeline.py`
- Keep for documentation purposes

---

## 💡 Alternative: Examples Directory

Create organized examples:

```
examples/
├── demo_pipeline.py          # Combined demo (merged from demo_*.py)
├── custom_chunking.py         # Example of custom chunker
├── custom_embeddings.py       # Example of custom embedder
└── README.md                  # Examples documentation
```

This keeps examples separate from operational scripts.

---

## ✅ Recommended Action

**For GitHub Upload:**

1. **Keep all 11 scripts** if you want comprehensive examples
2. **Remove 2 demo scripts** if you want lean codebase
3. **Move demos to `examples/`** if you want organization

**My recommendation:** **Move demos to `examples/`**

**Reasoning:**
- Keeps scripts focused on operations
- Separates examples from tools
- Makes purpose clearer for new users
- Easy to expand examples later

---

**Last Updated:** 2025-10-21
**Total Scripts:** 11
**Essential:** 5
**Useful:** 4
**Optional:** 2
