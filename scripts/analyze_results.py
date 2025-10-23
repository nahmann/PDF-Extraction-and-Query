"""
Quick analysis of evaluation results to help with manual scoring.

Shows key insights about similarity scores, chunk sizes, and document relevance.

Usage:
    python scripts/analyze_results.py evaluation/results_20251020_232926.json
"""

import sys
import json
from collections import defaultdict
from pathlib import Path


def analyze_results(results_file: str):
    """Analyze evaluation results and print insights"""

    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['results']

    print("\n" + "="*80)
    print("EVALUATION RESULTS ANALYSIS")
    print("="*80)

    # Basic stats
    print(f"\nQueries Tested: {data['summary']['total_queries']}")
    print(f"Avg Search Time: {data['summary']['avg_search_time_ms']:.0f}ms")
    print(f"Avg Results per Query: {data['summary']['avg_results_per_query']:.1f}")

    # Similarity score distribution
    print("\n" + "-"*80)
    print("SIMILARITY SCORE ANALYSIS")
    print("-"*80)

    all_similarities = []
    top1_similarities = []

    for result in results:
        if result['status'] == 'success':
            for i, res in enumerate(result['results']):
                all_similarities.append(res['similarity'])
                if i == 0:
                    top1_similarities.append(res['similarity'])

    if all_similarities:
        print(f"\nAll Results:")
        print(f"  Min: {min(all_similarities):.3f}")
        print(f"  Max: {max(all_similarities):.3f}")
        print(f"  Avg: {sum(all_similarities)/len(all_similarities):.3f}")

        # Distribution
        excellent = len([s for s in all_similarities if s > 0.8])
        good = len([s for s in all_similarities if 0.6 <= s <= 0.8])
        moderate = len([s for s in all_similarities if 0.4 <= s < 0.6])
        weak = len([s for s in all_similarities if s < 0.4])

        print(f"\n  Distribution:")
        print(f"    Excellent (>0.8): {excellent} ({excellent/len(all_similarities)*100:.1f}%)")
        print(f"    Good (0.6-0.8):   {good} ({good/len(all_similarities)*100:.1f}%)")
        print(f"    Moderate (0.4-0.6): {moderate} ({moderate/len(all_similarities)*100:.1f}%)")
        print(f"    Weak (<0.4):      {weak} ({weak/len(all_similarities)*100:.1f}%)")

    if top1_similarities:
        print(f"\nTop-1 Results Only:")
        print(f"  Avg: {sum(top1_similarities)/len(top1_similarities):.3f}")
        excellent_top1 = len([s for s in top1_similarities if s > 0.8])
        print(f"  Excellent (>0.8): {excellent_top1}/{len(top1_similarities)}")

    # Chunk size analysis
    print("\n" + "-"*80)
    print("CHUNK SIZE ANALYSIS")
    print("-"*80)

    chunk_lengths = []
    for result in results:
        if result['status'] == 'success':
            for res in result['results']:
                chunk_lengths.append(len(res['text']))

    if chunk_lengths:
        print(f"\nChunk Lengths (characters):")
        print(f"  Min: {min(chunk_lengths)}")
        print(f"  Max: {max(chunk_lengths)}")
        print(f"  Avg: {sum(chunk_lengths)/len(chunk_lengths):.0f}")

        # Show distribution
        very_short = len([l for l in chunk_lengths if l < 100])
        short = len([l for l in chunk_lengths if 100 <= l < 300])
        medium = len([l for l in chunk_lengths if 300 <= l < 600])
        long = len([l for l in chunk_lengths if l >= 600])

        print(f"\n  Distribution:")
        print(f"    Very Short (<100 chars): {very_short} ({very_short/len(chunk_lengths)*100:.1f}%)")
        print(f"    Short (100-300 chars):   {short} ({short/len(chunk_lengths)*100:.1f}%)")
        print(f"    Medium (300-600 chars):  {medium} ({medium/len(chunk_lengths)*100:.1f}%)")
        print(f"    Long (600+ chars):       {long} ({long/len(chunk_lengths)*100:.1f}%)")

    # Document frequency
    print("\n" + "-"*80)
    print("MOST FREQUENTLY RETRIEVED DOCUMENTS")
    print("-"*80)

    doc_counts = defaultdict(int)
    for result in results:
        if result['status'] == 'success':
            for res in result['results']:
                doc_counts[res['document_name']] += 1

    # Top 10 documents
    sorted_docs = sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 documents appearing in results:")
    for doc, count in sorted_docs:
        print(f"  {count:2d}x - {doc}")

    # Category analysis
    print("\n" + "-"*80)
    print("BY CATEGORY")
    print("-"*80)

    for category, stats in data['by_category'].items():
        print(f"\n{category}:")
        print(f"  Queries: {stats['total']}")
        print(f"  Successful: {stats['successful']}")

    # Flag potential issues
    print("\n" + "-"*80)
    print("POTENTIAL ISSUES TO INVESTIGATE")
    print("-"*80)

    issues = []

    # Low similarity scores
    if top1_similarities:
        avg_top1 = sum(top1_similarities) / len(top1_similarities)
        if avg_top1 < 0.6:
            issues.append(f"[WARNING] Low top-1 similarity avg ({avg_top1:.3f}) - embeddings may not be capturing semantics well")

    # Small chunks
    if chunk_lengths:
        avg_chunk = sum(chunk_lengths) / len(chunk_lengths)
        if avg_chunk < 200:
            issues.append(f"[WARNING] Very small chunks (avg {avg_chunk:.0f} chars) - answers likely incomplete")

    # Slow search
    if data['summary']['avg_search_time_ms'] > 1000:
        issues.append(f"[WARNING] Slow search ({data['summary']['avg_search_time_ms']:.0f}ms) - target <500ms")

    # No high-confidence results
    high_conf = len([s for s in top1_similarities if s > 0.8])
    if high_conf == 0:
        issues.append(f"[WARNING] No top-1 results with >0.8 similarity - may need better chunking or embeddings")

    if issues:
        for issue in issues:
            print(f"\n{issue}")
    else:
        print("\n[OK] No obvious issues detected - system looks good!")

    # Sample queries to review
    print("\n" + "-"*80)
    print("QUERIES TO REVIEW MANUALLY")
    print("-"*80)

    print("\nHigh Priority (Low Similarity):")
    low_sim_queries = []
    for result in results:
        if result['status'] == 'success' and result['results']:
            top_sim = result['results'][0]['similarity']
            if top_sim < 0.5:
                low_sim_queries.append((result['query_id'], result['query'], top_sim))

    low_sim_queries.sort(key=lambda x: x[2])
    for qid, query, sim in low_sim_queries[:5]:
        print(f"\n  Query {qid} (sim: {sim:.3f}):")
        print(f"  {query[:70]}...")

    print("\n\nHigh Priority (High Similarity - Should be Good):")
    high_sim_queries = []
    for result in results:
        if result['status'] == 'success' and result['results']:
            top_sim = result['results'][0]['similarity']
            if top_sim > 0.7:
                high_sim_queries.append((result['query_id'], result['query'], top_sim))

    high_sim_queries.sort(key=lambda x: x[2], reverse=True)
    for qid, query, sim in high_sim_queries[:5]:
        print(f"\n  Query {qid} (sim: {sim:.3f}):")
        print(f"  {query[:70]}...")

    print("\n" + "="*80)
    print("\nNext Steps:")
    print("1. Open evaluation/EVALUATION_NOTES_TEMPLATE.md")
    print("2. Manually score the queries listed above")
    print("3. Calculate average score to decide on chunking changes")
    print("4. Use: python scripts/evaluate_queries.py --interactive")
    print("   for easier interactive scoring")
    print("="*80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_results.py <results_file.json>")
        sys.exit(1)

    results_file = sys.argv[1]
    if not Path(results_file).exists():
        print(f"Error: File not found: {results_file}")
        sys.exit(1)

    analyze_results(results_file)
