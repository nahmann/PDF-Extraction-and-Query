# Chunker Comparison

You asked a great question: **"Why create a new SimpleChunker when we could just use LangChain without section awareness?"**

**Answer:** You're absolutely right! LangChain's `RecursiveCharacterTextSplitter` already does what SimpleChunker does, and it's better because it tries to split at smart boundaries.

## The Better Solution

Instead of creating a new chunker, I've modified `LangChainChunker` to support **both modes**:

### 1. `langchain` (Section-Aware - Original)
```python
CHUNKER_TYPE="langchain"
```
- Splits by section headers FIRST (##, ###, ####)
- Only splits further if section exceeds max_chunk_size
- **Problem:** Creates tiny chunks when sections are small (avg 215 chars)

### 2. `langchain_simple` (Size-Based - NEW RECOMMENDED)
```python
CHUNKER_TYPE="langchain_simple"
```
- Skips section header detection
- Uses LangChain's `RecursiveCharacterTextSplitter` directly
- **Result:** Consistent chunk sizes (~800-1000 chars)

## Why LangChain is Better Than My SimpleChunker

### LangChain's RecursiveCharacterTextSplitter
- Tries to split at smart boundaries in **order of preference**:
  1. `\n\n` (paragraphs)
  2. `\n` (lines)
  3. `. ` (sentences)
  4. ` ` (words)
  5. `` (hard cutoff if nothing else works)

### My SimpleChunker
- Hard cutoff at max_chunk_size
- Doesn't try sentence/paragraph boundaries
- Simpler, but less intelligent

### My SmartSimpleChunker
- Tries to find sentence boundaries
- Only looks back 100 chars
- Less sophisticated than LangChain's recursive approach

## Comparison Table

| Chunker | Splits at Sections? | Splits Smartly? | Consistency | Best For |
|---------|---------------------|-----------------|-------------|----------|
| `langchain` | ✓ Yes | ✓ Yes | ✗ Variable | Structured docs where sections matter |
| `langchain_simple` | ✗ No | ✓ Yes (paragraphs → sentences) | ✓ Consistent | Most RAG use cases |
| `simple` | ✗ No | ✗ No (hard cutoff) | ✓✓ Very Consistent | When you need exact sizes |
| `smart_simple` | ✗ No | ~ Partial (sentences only) | ✓ Consistent | Middle ground |

## Recommendation

**Use `langchain_simple`** - It's the best of both worlds:
- ✓ Consistent chunk sizes (what we need)
- ✓ Smart splitting at natural boundaries (better than hard cutoffs)
- ✓ Uses battle-tested LangChain code
- ✓ No need for custom chunker code

## Current Configuration

**File:** [src/config/settings.py](../src/config/settings.py#L30-L32)

```python
max_chunk_size: 1000
chunk_overlap: 200
chunker_type: "langchain_simple"  # RECOMMENDED
```

This will give you:
- Chunks averaging ~800-1000 chars
- Split at paragraph/sentence boundaries when possible
- Consistent sizes across all documents

## The Code Change

I modified `LangChainChunker.__init__` to accept `use_section_awareness`:

```python
def __init__(
    self,
    max_chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    use_section_awareness: bool = True,  # NEW parameter
    debug: bool = False
):
    ...
```

Then in `chunk()` method:
```python
if not self.use_section_awareness:
    # Skip all the markdown header detection
    # Go straight to RecursiveCharacterTextSplitter
    return self._fallback_chunk(text, base_metadata)
```

## Should You Keep SimpleChunker?

**Keep it for now** because:
1. It's already written (no harm in having it)
2. It's simpler to understand (good for documentation/examples)
3. Some users might want the absolute simplest option

But **use `langchain_simple` in production** - it's smarter and better tested.

## Testing the Difference

Let's compare all four chunkers on the same text:

```python
from chunking import create_chunker

text = "Section 1: Overview\n\nThis is the first paragraph of the overview section. It contains important information.\n\nThis is the second paragraph.\n\nSection 2: Details\n\nHere are the details..." * 100

# Test each chunker
for chunker_type in ["langchain", "langchain_simple", "simple", "smart_simple"]:
    chunker = create_chunker(chunker_type=chunker_type, max_chunk_size=1000)
    chunks = chunker.chunk(text)
    avg_size = sum(c['chunk_size'] for c in chunks) / len(chunks)
    print(f"{chunker_type:20s} -> {len(chunks):3d} chunks, avg {avg_size:6.1f} chars")
```

Expected results:
- `langchain`: ~50 chunks (small sections)
- `langchain_simple`: ~10 chunks (consistent ~900 chars)
- `simple`: ~10 chunks (consistent but may cut mid-sentence)
- `smart_simple`: ~10 chunks (consistent, tries sentences)

## Bottom Line

You were right to question creating a new chunker! **Use `langchain_simple`** - it's already configured as your default.
