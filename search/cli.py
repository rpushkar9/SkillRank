#!/usr/bin/env python3
"""
Command-line interface for the Skills Search Engine.

Usage:
    python cli.py "your search query"
    python cli.py "react testing" --top-k 5
    python cli.py "deployment" --verbose
"""

import sys
import argparse
from search_engine import SkillSearchEngine


def format_number(num: float) -> str:
    """Format large numbers with K/M suffixes."""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{num:.0f}"


def print_results(results, verbose=False):
    """
    Print search results in a formatted way.
    
    Args:
        results: List of result dictionaries
        verbose: Show detailed scoring breakdown
    """
    if not results:
        print("\nNo results found.")
        return
    
    print(f"\n{'='*80}")
    print(f"TOP {len(results)} RECOMMENDATIONS")
    print(f"{'='*80}")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['name']}")
        print(f"   {'─' * 70}")
        
        # Description (truncate if too long)
        desc = result['description']
        if len(desc) > 200:
            desc = desc[:197] + "..."
        print(f"   {desc}")
        
        # Metadata
        print(f"\n   📊 Weekly installs: {format_number(result['weekly_installs'])}")
        print(f"   📈 Total installs: {format_number(result['total_installs'])}")
        print(f"   📅 First seen: {result['first_seen']}")
        print(f"   🔗 URL: {result['skill_url']}")
        
        # Score
        print(f"\n   ⭐ Relevance Score: {result['final_score']:.4f}")
        
        # Detailed breakdown if verbose
        if verbose:
            breakdown = result['score_breakdown']
            print(f"      • Retrieval match: {breakdown['retrieval']:.3f}")
            print(f"      • Title match: {breakdown['title_match']:.3f}")
            print(f"      • Stage 1 score: {breakdown.get('stage1_score', 0):.3f}")
            
            # Show if popularity boost was applied
            boost_applied = breakdown.get('boost_applied', False)
            if boost_applied:
                print(f"      • Popularity boost: ✓ APPLIED (retrieval >= threshold)")
                print(f"        - Recency: {breakdown['recency']:.3f}")
                print(f"        - Weekly popularity: {breakdown['weekly_installs']:.3f}")
                print(f"        - Total popularity: {breakdown['total_installs']:.3f}")
            else:
                print(f"      • Popularity boost: ✗ NOT APPLIED (retrieval < threshold)")
                print(f"        - Recency: {breakdown['recency']:.3f} (not used)")
                print(f"        - Weekly popularity: {breakdown['weekly_installs']:.3f} (not used)")
                print(f"        - Total popularity: {breakdown['total_installs']:.3f} (not used)")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Search and rank skills using hybrid retrieval',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "react testing"
  python cli.py "vitest" --top-k 5
  python cli.py "deployment kubernetes" --verbose
        """
    )
    
    parser.add_argument(
        'query',
        type=str,
        help='Search query string'
    )
    
    parser.add_argument(
        '--top-k',
        type=int,
        default=3,
        help='Number of results to return (default: 3)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed scoring breakdown'
    )
    
    parser.add_argument(
        '--names-only',
        action='store_true',
        help='Output only skill names (one per line)'
    )
    
    parser.add_argument(
        '--data-path',
        type=str,
        default=None,
        help='Path to skills_raw.jsonl file (optional)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize search engine
        if not args.names_only:
            print("Initializing search engine...")
            print("(This may take a moment on first run to generate embeddings)")
            print()
        
        engine = SkillSearchEngine(skills_data_path=args.data_path)
        
        # Perform search
        if not args.names_only:
            print(f"\n🔍 Searching for: '{args.query}'")
        
        results = engine.search(args.query, top_k=args.top_k, verbose=False)
        
        # Output results
        if args.names_only:
            # Simple output: just names
            for result in results:
                print(result['name'])
        else:
            # Formatted output
            print_results(results, verbose=args.verbose)
            print(f"\n{'='*80}\n")
    
    except KeyboardInterrupt:
        print("\n\nSearch interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
