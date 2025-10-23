# Chunking Strategy Comparison Results

**Goal:** Find the optimal chunking strategy for M&A due diligence RAG system

## Test Configurations

### Test 1: Section-Aware (Original)
- **File:** `results_langchain_section_aware_215.json`
- **Date:** 2025-10-20
- **Chunker:** `langchain` (section-aware)
- **Settings:**
  - Max chunk size: 2000 chars
  - Chunk overlap: 200 chars
  - **Reality:** Avg 215 chars (sections were naturally small)
- **Strategy:** Split by document sections (##, ###) first, only split further if >2000 chars

### Test 2: Size-Based Large Chunks
- **File:** `results_langchain_simple_2000.json`
- **Date:** 2025-10-21
- **Chunker:** `langchain_simple` (size-based)
- **Settings:**
  - Max chunk size: 2000 chars
  - Chunk overlap: 200 chars
  - **Reality:** Avg 1,482 chars (consistent)
- **Strategy:** Ignore sections, split purely by size with smart boundaries (paragraphs → sentences)

### Test 3: Size-Based Medium Chunks
- **File:** `results_langchain_simple_1000.json`
- **Date:** 2025-10-21
- **Chunker:** `langchain_simple` (size-based)
- **Settings:**
  - Max chunk size: 1000 chars
  - Chunk overlap: 200 chars
  - **Reality:** Avg 814 chars (consistent)
- **Strategy:** Same as Test 2, but smaller max size

## Results Comparison

### Overall Performance

| Metric | Test 1: Section-Aware (215 chars) | Test 2: Size-Based (1,482 chars) | Test 3: Size-Based (814 chars) |
|--------|-----------------------------------|----------------------------------|--------------------------------|
| **Avg Chunk Size** | 215 chars | 1,482 chars | 814 chars |
| **Total Chunks** | 7,431 | 1,440 | 2,983 |
| **Chunks/Document** | 14.7 | 2.9 | 6.1 |
| **Top-1 Avg Similarity** | **0.580** 🥇 | 0.508 ❌ | **0.516** 🥈 |
| **All Results Avg Similarity** | **0.536** 🥇 | 0.464 ❌ | **0.485** 🥈 |
| **Search Time** | 2,118ms | 2,085ms | 2,123ms |

### Similarity Score Distribution

| Score Range | Test 1 (215 chars) | Test 2 (1,482 chars) | Test 3 (814 chars) |
|-------------|-------------------|---------------------|-------------------|
| **Excellent (>0.8)** | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| **Good (0.6-0.8)** | 21 (24.7%) 🥇 | 5 (5.9%) ❌ | 4 (4.7%) ❌ |
| **Moderate (0.4-0.6)** | 54 (63.5%) | 63 (74.1%) | 67 (78.8%) |
| **Weak (<0.4)** | 10 (11.8%) 🥇 | 17 (20.0%) ❌ | 14 (16.5%) 🥈 |

### Chunk Size Distribution

| Size Range | Test 1 (215 chars) | Test 2 (1,482 chars) | Test 3 (814 chars) |
|------------|-------------------|---------------------|-------------------|
| **Very Short (<100)** | 12 (14.1%) | 0 (0.0%) | 0 (0.0%) |
| **Short (100-300)** | 56 (65.9%) | 0 (0.0%) | 1 (1.2%) |
| **Medium (300-600)** | 16 (18.8%) | 9 (10.6%) | 10 (11.8%) |
| **Long (600+)** | 1 (1.2%) | 76 (89.4%) | 74 (87.1%) |

## Key Findings

### Test 1: Section-Aware (215 chars) - BEST SO FAR

**Strengths:**
- ✅ **Highest similarity scores** (0.580 top-1, 0.536 avg)
- ✅ **More "good" matches** (24.7% in 0.6-0.8 range)
- ✅ **Fewer weak matches** (11.8% below 0.4)
- ✅ **Semantically coherent** - each chunk is one complete section/idea

**Weaknesses:**
- ❌ Very small chunks (avg 215 chars)
- ❌ Chunks may not be "self-contained" answers
- ❌ Many chunks per document (14.7 avg)

**Why it worked:**
- Section boundaries preserve semantic coherence
- Each chunk focused on ONE topic → better embedding match
- Even though small, they're precise

### Test 2: Size-Based Large (1,482 chars) - WORST

**Strengths:**
- ✅ Larger chunks (more complete information)
- ✅ Consistent sizes (89.4% are 600+ chars)
- ✅ Fewer chunks to search through (2.9/doc vs 14.7/doc)

**Weaknesses:**
- ❌ **Similarity scores dropped 12%** (0.580 → 0.508)
- ❌ **Fewer good matches** (24.7% → 5.9% in good range)
- ❌ **More weak matches** (11.8% → 20.0% weak)
- ❌ Signal dilution - each chunk has multiple topics

**Why it failed:**
- Large chunks contain multiple ideas → embeddings average out
- Specific query signals get "buried" in chunk noise
- Less focused semantic meaning per chunk

### Test 3: Size-Based Medium (814 chars) - MIDDLE GROUND

**Performance:** Between Test 1 and Test 2 (as predicted)

**Strengths:**
- ✅ **Better than Test 2** (0.516 vs 0.508 top-1 similarity)
- ✅ **Fewer weak matches** than Test 2 (16.5% vs 20.0%)
- ✅ More chunks per doc than Test 2 (6.1 vs 2.9) = better coverage
- ✅ Smaller than Test 2 (814 vs 1,482 chars) = less signal dilution

**Weaknesses:**
- ❌ **Still worse than Test 1** (0.516 vs 0.580 = 11% lower)
- ❌ **Very few "good" matches** (4.7% in 0.6-0.8 range vs 24.7%)
- ❌ **Most chunks still large** (87.1% are 600+ chars)
- ❌ Signal dilution still present (just less than Test 2)

**Why it's better than Test 2 but not Test 1:**
- Reducing from 1,482 → 814 chars helps (less dilution)
- But still 3.8x larger than Test 1's 215 chars
- Embeddings still averaging over multiple ideas/topics per chunk
- Doesn't reach the semantic coherence of section-based chunking

## Analysis: Why Did Larger Chunks Hurt?

### Embedding Model Limitations
- **Model:** sentence-transformers/all-MiniLM-L6-v2
- **Vector size:** 384 dimensions
- **Designed for:** Sentences/short passages (not long documents)

When encoding 1,482 chars vs 215 chars:
- Same 384-dimensional vector must capture 6.8x more information
- Results in **averaging/pooling** across more diverse content
- Specific signals get diluted

### Example

**Query:** "What are stock option vesting terms?"

**Test 1 (215 chars, section-aware):**
```
Chunk: "Options vest over four years with a one-year cliff.
25% vest after 12 months, then 1/48th monthly thereafter."
Similarity: 0.75 (focused signal)
```

**Test 2 (1,482 chars, size-based):**
```
Chunk: "[Compensation Policy] Salaries reviewed annually...
bonuses based on performance... health insurance...
401k matching... [buried in middle] options vest over
four years... vacation policy 15 days... remote work..."
Similarity: 0.52 (signal diluted by surrounding content)
```

The embedding "sees" the whole chunk, so the vesting info is just 10% of the signal.

## Recommendations

### Option A: Stick with Test 1 (Section-Aware)
**If:** Similarity scores are most important

**Action:**
- Keep `chunker_type="langchain"` (section-aware)
- Accept that chunks are small
- Post-process results to combine consecutive chunks from same document

**Pros:** Best similarity scores (proven)
**Cons:** Small chunks, may need multiple results to answer questions

### Option B: Try Test 3 (Medium Size-Based)
**If:** Want to find sweet spot

**Action:**
- Keep `chunker_type="langchain_simple"`
- Use `MAX_CHUNK_SIZE=1000`
- Test and compare to Test 1 and Test 2

**Pros:** Might balance size and focus
**Cons:** Unknown if it will improve on Test 1

### Option C: Hybrid Approach (Best of Both)
**If:** Want semantic coherence AND completeness

**Action:**
- Modify `langchain` chunker to merge small sections
- Keep section boundaries but enforce min_chunk_size=400, max_chunk_size=1000
- This preserves semantic coherence while ensuring adequate size

**Pros:** Best of both worlds (focused + complete)
**Cons:** Requires code changes

### Option D: Keep Test 1, Add Re-ranking
**If:** Want to improve answer quality without changing chunks

**Action:**
- Use Test 1 chunking (best similarity)
- Add second-stage re-ranking to find best answer within top 10 results
- Combine consecutive chunks from same document

**Pros:** Improves final results without re-chunking
**Cons:** More complex query pipeline

## Next Steps

### Completed
1. ✅ Renamed files to reflect actual chunk sizes
2. ✅ Run Test 3 (1000 char max) to complete comparison
3. ✅ Analyze Test 3 results
4. ⏳ Make final decision on chunking strategy

### Test 3 Results Confirmed

**Result: Test 1 > Test 3 > Test 2** (as predicted)

Rankings:
- 🥇 **Test 1 (section-aware, 215 chars): 0.580 similarity**
- 🥈 **Test 3 (size-based, 814 chars): 0.516 similarity** (-11%)
- 🥉 **Test 2 (size-based, 1,482 chars): 0.508 similarity** (-12%)

**Conclusion:** Section-aware chunking is clearly superior for this use case.

### Recommended Next Steps

**DECISION: Use Test 1 (Section-Aware) as base strategy**

Consider implementing:
1. **Option C (Hybrid)**: Modify section-aware chunker to merge tiny sections (min 300 chars) while preserving semantic boundaries
2. **Option D (Re-ranking)**: Keep Test 1 chunks, add post-processing to combine consecutive chunks from same document
3. **Accept Test 1 as-is**: Best similarity scores, can retrieve top-10 results to ensure coverage

## Files

### Evaluation Results
- `results_langchain_section_aware_215.json` - Test 1 (section-aware, 215 chars avg) ✅
- `results_langchain_simple_2000.json` - Test 2 (size-based large, 1,482 chars avg) ✅
- `results_langchain_simple_1000.json` - Test 3 (size-based medium, 814 chars avg) ✅

### Analysis Scripts
```bash
# Analyze each result
python scripts/analyze_results.py evaluation/results_langchain_section_aware_215.json
python scripts/analyze_results.py evaluation/results_langchain_simple_2000.json
python scripts/analyze_results.py evaluation/results_langchain_simple_1000.json

# Compare side-by-side
diff evaluation/results_langchain_section_aware_215.json evaluation/results_langchain_simple_2000.json
```

## Final Conclusion

### Key Finding: Semantic Coherence > Information Completeness

**All three tests complete.** Section-aware chunking with small chunks (215 chars avg) outperformed both size-based approaches:

| Strategy | Avg Chunk Size | Top-1 Similarity | Performance |
|----------|---------------|------------------|-------------|
| **Section-Aware** | 215 chars | **0.580** | 🥇 Best |
| **Size-Based (Medium)** | 814 chars | 0.516 | 🥈 11% worse |
| **Size-Based (Large)** | 1,482 chars | 0.508 | 🥉 12% worse |

### Why Section-Aware Won

1. **Semantic Boundaries:** Chunks align with document structure (## headings)
2. **Single Topic per Chunk:** Each embedding represents ONE coherent idea
3. **No Signal Dilution:** 384-dim embedding model focuses on specific content
4. **Better Matches:** 24.7% of results in "good" range (0.6-0.8) vs <5% for size-based

### Why Size-Based Failed

Even medium-sized chunks (814 chars) still:
- Contain multiple topics → embeddings average out
- Dilute specific signals across unrelated content
- Struggle with 384-dim embedding limitation
- Can't match semantic precision of section boundaries

### Recommendation

**Use Test 1 configuration:**
```env
CHUNKER_TYPE=langchain
MAX_CHUNK_SIZE=2000
CHUNK_OVERLAP=200
```

This preserves section boundaries while allowing large sections to be split if needed. The avg 215 chars is a natural result of document structure, not a constraint.

---

**Last Updated:** 2025-10-21
**Status:** ✅ All 3 tests complete - Section-aware chunking confirmed as optimal
