# RAG System Evaluation Notes

**Date:** 2025-10-20
**Test Run:** Critical Priority Queries (17 of 40)
**Results File:** `results_20251020_232926.json`

## Quick Stats

- **Total Queries Tested:** 17 (critical priority only)
- **Success Rate:** 100% (17/17)
- **Avg Search Time:** 2,118ms (~2.1 seconds)
- **Avg Results per Query:** 5.0

## What to Look For in Results

### 1. Similarity Scores
- **>0.8** = Excellent match (semantically very similar)
- **0.6-0.8** = Good match (relevant and on-topic)
- **0.4-0.6** = Moderate match (related but may be indirect)
- **<0.4** = Weak match (might be off-topic)

### 2. Chunk Quality
Ask yourself for each result:
- [ ] Does the chunk **answer the question directly**?
- [ ] Does the chunk **contain complete information**, or just point to a location?
- [ ] Is the chunk **readable and self-contained**?
- [ ] Would you need to click through to the PDF to get the real answer?

### 3. Document Relevance
- Are the **right documents** being retrieved?
- Check `expected_docs` in `ma_test_queries.json` - do results match?
- Are there important documents **missing** from results?

## Sample Query Analysis

### Query 1: "What is the current corporate structure and ownership?"

**Top Result:**
- **Similarity:** 0.601 (Moderate-Good)
- **Document:** series-c-preferred-stock-purchase-agreement.pdf ✓ (expected)
- **Text:** "The Company is a corporation duly organized, validly existing, and in good standing under the laws of Delaware..."

**Notes:**
- ✓ Right document type (funding agreements)
- ✗ **Chunk is too generic** - talks about Delaware corp status, not ownership details
- ✓ Result #5 has actual ownership percentages (Quantum Ventures 18.5%, etc.)
- **Issue:** Best answer is rank #5, not rank #1
- **Score:** Would rate this 2/4 - relevant but incomplete

**What this tells us:**
- Embeddings are finding relevant documents ✓
- Chunk ordering could be better (specific data should rank higher)
- Chunks averaging 176 chars might be too small for complete answers

---

## Evaluation Template (Copy for Each Query)

### Query ID: ___

**Question:** _________________________________________________

**Expected Documents:** _______________________________________

**Top Result Analysis:**
- Similarity Score: ______
- Document: _____________________
- Chunk Index: ______
- Text Preview: _________________________________________________

**Manual Score (0-4):** ___
- [ ] 0 - No relevant results
- [ ] 1 - Partially relevant (mentions topic, no details)
- [ ] 2 - Relevant but incomplete
- [ ] 3 - Good answer (most key info present)
- [ ] 4 - Excellent (complete, self-contained)

**Notes:**
- Right document retrieved? Y/N
- Answer complete? Y/N
- Issues: ___________________________________________________
- Better result in lower ranks? Y/N - which rank? ___

---

## Overall Observations

### Strengths
- [ ] System finds relevant documents consistently
- [ ] Search time is acceptable (<3s per query)
- [ ] No errors or failures
- [ ] Chunk metadata includes useful section info

### Weaknesses
- [ ] Chunks too small (avg 176 chars) - answers incomplete
- [ ] Similarity scores moderate (0.4-0.6) not high (>0.8)
- [ ] Best answers often not rank #1
- [ ] Need more context to understand chunks

### Patterns Noticed

**Document Types:**
- Which document types work well: _______________________
- Which document types work poorly: _____________________

**Query Types:**
- Factual questions (names, dates, numbers): Score ___/4
- Conceptual questions (explain/describe): Score ___/4
- Location questions (find specific clause): Score ___/4

**Chunk Issues:**
- [ ] Chunks cut off mid-sentence
- [ ] Missing important context from surrounding text
- [ ] Section headers without content (or vice versa)
- [ ] Multiple related chunks should be combined

## Critical Issues to Address

Priority issues that need fixing:

1. **Issue:** _______________________________________________
   - **Impact:** High/Medium/Low
   - **Fix:** ______________________________________________

2. **Issue:** _______________________________________________
   - **Impact:** High/Medium/Low
   - **Fix:** ______________________________________________

## Performance Analysis

### Search Time: 2,118ms average
- **Expected:** <500ms for production systems
- **Current:** ~2 seconds (4x slower than target)
- **Possible causes:**
  - [ ] First-time embedding model load
  - [ ] Database not indexed properly
  - [ ] Network latency (Docker on Windows)
  - [ ] Result enrichment (fetching doc metadata)

**Action:** Profile to find bottleneck

### Result Relevance
- **Top-1 Accuracy:** ___% (how often is rank #1 the best answer?)
- **Top-3 Accuracy:** ___% (how often is answer in top 3?)
- **Top-5 Accuracy:** ___% (answer in top 5?)

## Scoring Summary (After Manual Review)

Fill this in after you manually score all queries:

| Category | Queries | Avg Score | Notes |
|----------|---------|-----------|-------|
| Corporate Structure | 1 | ___ | |
| Funding History | 2 | ___ | |
| Equity & Compensation | 1 | ___ | |
| Key Employees | 1 | ___ | |
| Intellectual Property | 2 | ___ | |
| Customer Contracts | 2 | ___ | |
| Liabilities & Legal | 1 | ___ | |
| Financial Performance | 2 | ___ | |
| Debt & Obligations | 1 | ___ | |
| Regulatory & Compliance | 2 | ___ | |
| Data & Security | 1 | ___ | |
| Governance | 1 | ___ | |

**Overall Average Score:** ___/4.0

## Decision: What to Do Next?

Based on your evaluation results:

### If Avg Score ≥ 3.0 (System is good!)
- [ ] Test remaining 23 queries (high/medium/low priority)
- [ ] Consider chunking good enough
- [ ] Focus on performance optimization (reduce 2s search time)
- [ ] Move on to production features

### If Avg Score = 2.0-3.0 (System needs improvement)
- [ ] Increase chunk size (try 500-1000 chars instead of 176)
- [ ] Experiment with different chunking strategies
- [ ] Add re-ranking step after initial retrieval
- [ ] Consider hybrid search (keyword + semantic)
- [ ] Re-test after changes

### If Avg Score < 2.0 (System has issues)
- [ ] Review chunking completely - likely too small
- [ ] Check if embeddings are working correctly
- [ ] Verify all documents loaded properly
- [ ] Consider different embedding model
- [ ] May need fundamental architecture changes

## Next Steps

1. [ ] Manually score all 17 critical queries
2. [ ] Calculate average score
3. [ ] Decide on chunking changes needed
4. [ ] Test remaining 23 queries OR fix chunking first
5. [ ] Document final decisions

---

## Appendix: Quick Reference

### Scoring Guide
- **4:** "The stock options vest over 4 years with a 1-year cliff, 25% after year 1, then monthly." ✓
- **3:** "Stock options have vesting schedule detailed in the equity plan." (mostly there)
- **2:** "See stock option plan for vesting terms." (relevant pointer)
- **1:** "Options are granted to employees." (mentions topic, no answer)
- **0:** Completely wrong or no results

### Current System Specs
- Embedding Model: sentence-transformers/all-MiniLM-L6-v2
- Vector Dim: 384
- Chunker: LangChainChunker (section-aware)
- Max Chunk Size: 2000 chars (config) but actual avg: 176 chars
- Chunk Overlap: 200 chars
- Documents: 507 PDFs
- Total Chunks: 7,431
- Avg Chunks/Doc: 14.66

### Why Only 17 Queries Tested?

You ran with `--priority critical` flag, which filters to only critical priority queries.

**To test all 40 queries:**
```bash
python scripts/evaluate_queries.py --output evaluation/full_results.json
```

**Recommendation:**
- First, manually score these 17 critical queries
- If results are good (avg ≥3), test all 40
- If results are poor (avg <2), fix chunking FIRST, then re-test
