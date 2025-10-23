"""
Systematic evaluation of M&A test queries.

Tests all queries from evaluation/ma_test_queries.json against the RAG API
and generates a detailed evaluation report.

Usage:
    python scripts/evaluate_queries.py                    # Run all queries
    python scripts/evaluate_queries.py --category "IP"    # Filter by category
    python scripts/evaluate_queries.py --priority critical # Filter by priority
    python scripts/evaluate_queries.py --interactive      # Manual scoring mode
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import json
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
import argparse
from collections import defaultdict


class QueryEvaluator:
    """Evaluates RAG queries and generates reports"""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.results = []

    def load_queries(self, filepath: str) -> Dict:
        """Load M&A test queries from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_query(self, query_data: Dict, top_k: int = 5) -> Dict:
        """
        Execute a single query against the API

        Args:
            query_data: Query object from ma_test_queries.json
            top_k: Number of results to retrieve

        Returns:
            Dict with query, results, and metadata
        """
        query_text = query_data['query']

        try:
            start_time = time.time()

            response = requests.post(
                f"{self.api_url}/api/v1/search",
                json={
                    "query": query_text,
                    "top_k": top_k
                },
                timeout=30
            )

            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                return {
                    'query_id': query_data['id'],
                    'category': query_data['category'],
                    'priority': query_data['priority'],
                    'query': query_text,
                    'results': data['results'],
                    'total_results': data['total_results'],
                    'search_time_ms': elapsed_ms,
                    'status': 'success',
                    'expected_docs': query_data.get('expected_docs', []),
                    'why_important': query_data.get('why_important', ''),
                    'score': None  # To be filled in during evaluation
                }
            else:
                return {
                    'query_id': query_data['id'],
                    'category': query_data['category'],
                    'query': query_text,
                    'status': 'error',
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'score': 0
                }

        except Exception as e:
            return {
                'query_id': query_data['id'],
                'category': query_data['category'],
                'query': query_text,
                'status': 'error',
                'error': str(e),
                'score': 0
            }

    def run_evaluation(self, queries: List[Dict], top_k: int = 5,
                      category_filter: Optional[str] = None,
                      priority_filter: Optional[str] = None,
                      interactive: bool = False) -> List[Dict]:
        """
        Run evaluation on all queries

        Args:
            queries: List of query objects
            top_k: Number of results per query
            category_filter: Only test queries in this category
            priority_filter: Only test queries with this priority
            interactive: If True, prompt user to score each result

        Returns:
            List of results
        """
        # Filter queries
        filtered_queries = queries
        if category_filter:
            filtered_queries = [q for q in filtered_queries
                              if category_filter.lower() in q['category'].lower()]
        if priority_filter:
            filtered_queries = [q for q in filtered_queries
                              if q['priority'].lower() == priority_filter.lower()]

        print(f"\n{'='*80}")
        print(f"Running evaluation on {len(filtered_queries)} queries")
        print(f"{'='*80}\n")

        results = []

        for i, query_data in enumerate(filtered_queries, 1):
            print(f"\n[{i}/{len(filtered_queries)}] Testing query {query_data['id']}: {query_data['category']}")
            print(f"Query: {query_data['query']}")
            print(f"Priority: {query_data['priority']}")

            result = self.test_query(query_data, top_k=top_k)

            if result['status'] == 'success':
                print(f"[OK] Found {result['total_results']} results in {result['search_time_ms']:.0f}ms")

                # Show top results
                for j, res in enumerate(result['results'][:3], 1):
                    print(f"\n  Result {j} (similarity: {res['similarity']:.3f}):")
                    print(f"  Document: {res['document_name']}")
                    print(f"  Chunk Index: {res.get('chunk_index', 'N/A')}")
                    print(f"  Text: {res['text'][:150]}...")

                # Interactive scoring
                if interactive:
                    result['score'] = self._interactive_score(result)
                else:
                    result['score'] = None  # Manual scoring needed

            else:
                print(f"[ERROR] {result['error']}")

            results.append(result)
            time.sleep(0.5)  # Be nice to the API

        self.results = results
        return results

    def _interactive_score(self, result: Dict) -> int:
        """Prompt user to score a result interactively"""
        print("\n" + "="*60)
        print("SCORING RUBRIC:")
        print("0 = No relevant results")
        print("1 = Partially relevant - mentions topic but missing key details")
        print("2 = Relevant but incomplete")
        print("3 = Good answer - contains most key information")
        print("4 = Excellent answer - complete, self-contained")
        print("="*60)

        while True:
            try:
                score = input("\nEnter score (0-4) or 's' to skip: ").strip()
                if score.lower() == 's':
                    return None
                score = int(score)
                if 0 <= score <= 4:
                    return score
                print("Score must be between 0 and 4")
            except ValueError:
                print("Invalid input. Enter a number 0-4 or 's' to skip")

    def generate_report(self, output_file: Optional[str] = None) -> Dict:
        """
        Generate evaluation report

        Args:
            output_file: Optional path to save JSON report

        Returns:
            Report dictionary
        """
        if not self.results:
            print("No results to report")
            return {}

        # Calculate statistics
        total_queries = len(self.results)
        successful = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r['status'] == 'error']

        scored = [r for r in self.results if r.get('score') is not None]

        # Group by category
        by_category = defaultdict(list)
        for r in self.results:
            by_category[r['category']].append(r)

        # Group by priority
        by_priority = defaultdict(list)
        for r in self.results:
            by_priority[r['priority']].append(r)

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_queries': total_queries,
                'successful': len(successful),
                'failed': len(failed),
                'scored': len(scored),
                'avg_search_time_ms': sum(r.get('search_time_ms', 0) for r in successful) / len(successful) if successful else 0,
                'avg_results_per_query': sum(r.get('total_results', 0) for r in successful) / len(successful) if successful else 0,
            },
            'by_category': {},
            'by_priority': {},
            'results': self.results
        }

        # Category breakdown
        for category, results in by_category.items():
            category_scored = [r for r in results if r.get('score') is not None]
            report['by_category'][category] = {
                'total': len(results),
                'successful': len([r for r in results if r['status'] == 'success']),
                'scored': len(category_scored),
                'avg_score': sum(r['score'] for r in category_scored) / len(category_scored) if category_scored else None
            }

        # Priority breakdown
        for priority, results in by_priority.items():
            priority_scored = [r for r in results if r.get('score') is not None]
            report['by_priority'][priority] = {
                'total': len(results),
                'successful': len([r for r in results if r['status'] == 'success']),
                'scored': len(priority_scored),
                'avg_score': sum(r['score'] for r in priority_scored) / len(priority_scored) if priority_scored else None
            }

        # Add scoring summary if any scored
        if scored:
            scores = [r['score'] for r in scored]
            report['scoring'] = {
                'total_scored': len(scored),
                'avg_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'distribution': {
                    '0': len([s for s in scores if s == 0]),
                    '1': len([s for s in scores if s == 1]),
                    '2': len([s for s in scores if s == 2]),
                    '3': len([s for s in scores if s == 3]),
                    '4': len([s for s in scores if s == 4]),
                }
            }

        # Save to file
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\nReport saved to: {output_file}")

        return report

    def print_summary(self):
        """Print a human-readable summary to console"""
        if not self.results:
            print("No results to summarize")
            return

        report = self.generate_report()

        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)

        summary = report['summary']
        print(f"\nTotal Queries: {summary['total_queries']}")
        print(f"Successful: {summary['successful']} ({summary['successful']/summary['total_queries']*100:.1f}%)")
        print(f"Failed: {summary['failed']}")
        print(f"Avg Search Time: {summary['avg_search_time_ms']:.0f}ms")
        print(f"Avg Results per Query: {summary['avg_results_per_query']:.1f}")

        if 'scoring' in report:
            print("\n" + "-"*80)
            print("SCORING RESULTS")
            print("-"*80)
            scoring = report['scoring']
            print(f"Queries Scored: {scoring['total_scored']}/{summary['total_queries']}")
            print(f"Average Score: {scoring['avg_score']:.2f}/4.00")
            print(f"Score Range: {scoring['min_score']} - {scoring['max_score']}")
            print("\nScore Distribution:")
            for score, count in scoring['distribution'].items():
                bar = '#' * count
                print(f"  {score}: {bar} ({count})")

        print("\n" + "-"*80)
        print("BY CATEGORY")
        print("-"*80)
        for category, stats in report['by_category'].items():
            avg_score_str = f", Avg Score: {stats['avg_score']:.2f}" if stats['avg_score'] is not None else ""
            print(f"{category:30s} | Queries: {stats['total']:2d} | Success: {stats['successful']:2d}{avg_score_str}")

        print("\n" + "-"*80)
        print("BY PRIORITY")
        print("-"*80)
        for priority, stats in report['by_priority'].items():
            avg_score_str = f", Avg Score: {stats['avg_score']:.2f}" if stats['avg_score'] is not None else ""
            print(f"{priority:10s} | Queries: {stats['total']:2d} | Success: {stats['successful']:2d}{avg_score_str}")

        # Show failed queries if any
        failed = [r for r in self.results if r['status'] == 'error']
        if failed:
            print("\n" + "-"*80)
            print("FAILED QUERIES")
            print("-"*80)
            for r in failed:
                print(f"Query {r['query_id']}: {r['query']}")
                print(f"  Error: {r['error']}\n")

        # Show low-scoring queries if scored
        if 'scoring' in report:
            low_scores = [r for r in self.results if r.get('score') is not None and r['score'] <= 1]
            if low_scores:
                print("\n" + "-"*80)
                print("LOW-SCORING QUERIES (Score ≤ 1)")
                print("-"*80)
                for r in low_scores:
                    print(f"Query {r['query_id']} (Score: {r['score']}): {r['query']}")
                    print(f"  Category: {r['category']}, Priority: {r['priority']}\n")

        print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate M&A test queries against RAG API"
    )
    parser.add_argument(
        '--queries-file',
        default='evaluation/ma_test_queries.json',
        help='Path to queries JSON file'
    )
    parser.add_argument(
        '--api-url',
        default='http://localhost:8000',
        help='API base URL'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of results to retrieve per query'
    )
    parser.add_argument(
        '--category',
        help='Filter by category (e.g., "IP", "Corporate Structure")'
    )
    parser.add_argument(
        '--priority',
        choices=['critical', 'high', 'medium', 'low'],
        help='Filter by priority level'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Enable interactive scoring mode'
    )
    parser.add_argument(
        '--output',
        help='Output JSON report file path'
    )

    args = parser.parse_args()

    # Check if API is running
    evaluator = QueryEvaluator(api_url=args.api_url)

    try:
        response = requests.get(f"{args.api_url}/api/v1/health", timeout=5)
        if response.status_code != 200:
            print(f"ERROR: API health check failed. Is the server running at {args.api_url}?")
            print("Start the API with: python run_api.py")
            return 1
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Cannot connect to API at {args.api_url}")
        print(f"Error: {e}")
        print("\nStart the API with: python run_api.py")
        return 1

    # Load queries
    try:
        data = evaluator.load_queries(args.queries_file)
        queries = data['queries']
    except FileNotFoundError:
        print(f"ERROR: Queries file not found: {args.queries_file}")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to load queries: {e}")
        return 1

    # Run evaluation
    evaluator.run_evaluation(
        queries,
        top_k=args.top_k,
        category_filter=args.category,
        priority_filter=args.priority,
        interactive=args.interactive
    )

    # Generate report
    output_file = args.output
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"evaluation/results_{timestamp}.json"

    evaluator.generate_report(output_file)
    evaluator.print_summary()

    print(f"\n[DONE] Evaluation complete!")
    print(f"Results saved to: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
