# M&A Query Evaluation Guide

This guide explains how to use the evaluation script to systematically test all 40 M&A due diligence queries.

## Quick Start

### 1. Start the API
```bash
python run_api.py
```

Wait for: `Application startup complete`

### 2. Run All Queries (Non-Interactive)
```bash
python scripts/evaluate_queries.py
```

This will:
- Test all 40 queries
- Save results to `evaluation/results_YYYYMMDD_HHMMSS.json`
- Print a summary report

### 3. Run with Interactive Scoring
```bash
python scripts/evaluate_queries.py --interactive
```

After each query, you'll be prompted to score the results:
```
SCORING RUBRIC:
0 = No relevant results
1 = Partially relevant - mentions topic but missing key details
2 = Relevant but incomplete
3 = Good answer - contains most key information
4 = Excellent answer - complete, self-contained

Enter score (0-4) or 's' to skip:
```

## Usage Examples

### Test Only Critical Priority Queries
```bash
python scripts/evaluate_queries.py --priority critical
```

This tests only the 17 critical priority queries, useful for quick validation.

### Test Specific Category
```bash
python scripts/evaluate_queries.py --category "Intellectual Property"
```

Test only IP-related queries.

### Get More Results Per Query
```bash
python scripts/evaluate_queries.py --top-k 10
```

Retrieve top 10 results instead of default 5. Useful to see if relevant docs appear lower in rankings.

### Custom Output File
```bash
python scripts/evaluate_queries.py --output evaluation/my_test.json
```

### Combine Filters
```bash
python scripts/evaluate_queries.py --priority critical --top-k 10 --interactive
```

Test critical queries with 10 results each, with interactive scoring.

## Understanding the Output

### Console Output

During execution, you'll see:
```
[1/40] Testing query 1: Corporate Structure
Query: What is the current corporate structure and ownership?
Priority: critical
[OK] Found 5 results in 234ms

  Result 1 (similarity: 0.856):
  Document: certificate-of-incorporation.pdf
  Page: 3
  Text: The Company is a Delaware corporation...

  Result 2 (similarity: 0.792):
  Document: stockholder-agreement.pdf
  Page: 1
  Text: This Agreement sets forth the rights...
```

### Summary Report

At the end, you get:
```
EVALUATION SUMMARY
================================================================================
Total Queries: 40
Successful: 40 (100.0%)
Failed: 0
Avg Search Time: 245ms
Avg Results per Query: 8.2

BY CATEGORY
--------------------------------------------------------------------------------
Corporate Structure            | Queries:  5 | Success:  5
Intellectual Property          | Queries:  6 | Success:  6
Customer Contracts            | Queries:  4 | Success:  4
...

BY PRIORITY
--------------------------------------------------------------------------------
critical   | Queries: 17 | Success: 17
high       | Queries: 15 | Success: 15
medium     | Queries:  8 | Success:  8
```

If you ran with `--interactive`, you'll also see:
```
SCORING RESULTS
--------------------------------------------------------------------------------
Queries Scored: 40/40
Average Score: 2.85/4.00
Score Range: 1 - 4

Score Distribution:
  0:  (0)
  1: ## (2)
  2: ######### (9)
  3: ################## (18)
  4: ########### (11)
```

### JSON Output File

The JSON file contains detailed results for every query:
```json
{
  "timestamp": "2025-10-20T14:30:00",
  "summary": {
    "total_queries": 40,
    "successful": 40,
    "failed": 0,
    "avg_search_time_ms": 245,
    "avg_results_per_query": 8.2
  },
  "by_category": {
    "Corporate Structure": {
      "total": 5,
      "successful": 5,
      "scored": 5,
      "avg_score": 3.2
    }
  },
  "results": [
    {
      "query_id": 1,
      "category": "Corporate Structure",
      "query": "What is the current corporate structure?",
      "results": [
        {
          "chunk_id": "uuid",
          "document_name": "cert-of-incorporation.pdf",
          "text": "...",
          "similarity_score": 0.856,
          "page_number": 3
        }
      ],
      "total_results": 5,
      "search_time_ms": 234,
      "score": 3
    }
  ]
}
```

## Evaluation Workflow

### Recommended Approach

1. **First Pass - Quick Test**
   ```bash
   python scripts/evaluate_queries.py --priority critical
   ```
   Test just the 17 critical queries to see if system is working

2. **Second Pass - Full Evaluation**
   ```bash
   python scripts/evaluate_queries.py --interactive
   ```
   Test all 40 queries and score them interactively

3. **Analysis**
   - Review the JSON output file
   - Identify low-scoring queries (score ≤ 1)
   - Check if issues are related to:
     - Small chunk size (176 chars avg)
     - Missing documents
     - Poor chunking boundaries
     - Embedding quality

4. **Iteration**
   - Adjust chunking parameters if needed
   - Re-upload documents with new settings
   - Re-run evaluation to compare

### What to Look For

**Good Results (Score 3-4):**
- Chunk contains the answer or key details
- Document name matches expected doc types
- High similarity score (>0.8)
- Answer is self-contained

**Example:**
```
Query: "What are the stock option vesting terms?"
Result: "Options vest over four years with a one-year cliff. 25% vest after 12 months, then monthly vesting of 1/48th of the total grant."
Score: 4 (Excellent - complete answer)
```

**Poor Results (Score 0-1):**
- Chunk mentions topic but no details
- Wrong document retrieved
- Low similarity score (<0.6)
- Need to click through to find answer

**Example:**
```
Query: "What are the stock option vesting terms?"
Result: "See attached stock option plan for details."
Score: 1 (Points to doc but doesn't answer)
```

### Scoring Guidelines

**Score 4 (Excellent):**
- Complete, self-contained answer
- No need to look at original document
- All key details present

**Score 3 (Good):**
- Most key information present
- Minor details missing
- Generally satisfactory answer

**Score 2 (Relevant but Incomplete):**
- Right topic, right document
- Missing important details
- Need to read more chunks/pages

**Score 1 (Partially Relevant):**
- Mentions the topic
- No substantive information
- Basically just points to location

**Score 0 (No Relevant Results):**
- Wrong topic entirely
- No useful information
- System failed to find relevant docs

## Performance Benchmarks

Based on typical RAG systems with similar specs:

- **Search Time:** Should be <500ms per query
- **Result Relevance:** Top-1 hit should score ≥2 for 80% of queries
- **Coverage:** Should find relevant docs for 95%+ of queries

If your results fall short:
1. Check chunk size (might need larger chunks for complete answers)
2. Verify all 490 PDFs are properly loaded
3. Consider hybrid search (keyword + semantic)
4. Add query expansion or re-ranking

## Command Reference

```bash
# All commands assume you're in project root directory

# Full evaluation with all options
python scripts/evaluate_queries.py \
  --queries-file evaluation/ma_test_queries.json \
  --api-url http://localhost:8000 \
  --top-k 5 \
  --interactive \
  --output evaluation/my_results.json

# Quick test (critical queries only)
python scripts/evaluate_queries.py --priority critical

# Test specific category
python scripts/evaluate_queries.py --category "IP"

# Get help
python scripts/evaluate_queries.py --help
```

## Troubleshooting

### "Cannot connect to API"
- Make sure API is running: `python run_api.py`
- Check it's on port 8000: http://localhost:8000/docs
- Verify Docker is running (for pgVector database)

### "Queries file not found"
- Run from project root directory
- Check path: `evaluation/ma_test_queries.json` exists

### Slow queries (>1 second)
- Database might need indexing (should be automatic)
- Check Docker resources
- Verify embedding model is loaded once (not per query)

### All scores are low
- Chunks might be too small (176 chars avg)
- Consider re-chunking with larger max_chunk_size
- See chunking config in `src/core/config.py`

## Next Steps After Evaluation

Based on your results:

1. **If scores are mostly 3-4:** System is working well!
   - Move on to building frontend or additional features
   - Consider production deployment

2. **If scores are mostly 1-2:** Chunking needs improvement
   - Increase chunk size in config
   - Re-upload all documents
   - Re-run evaluation

3. **If scores are mostly 0:** Fundamental issues
   - Check if documents loaded correctly
   - Verify embeddings are working
   - Test with simpler queries first

4. **Mixed results:** Analyze by category
   - Some document types might chunk better than others
   - May need different chunking strategies per doc type
