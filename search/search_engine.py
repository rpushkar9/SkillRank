"""
Main search engine orchestrator.

Combines BM25 and vector retrieval, merges results, and applies reranking
to recommend the top 3 most relevant skills.
"""

from typing import List, Dict, Any, Tuple
from data_loader import load_skills, get_default_data_path
from bm25_retriever import BM25Retriever
from vector_retriever import VectorRetriever
from reranker import Reranker


class SkillSearchEngine:
    """
    Hybrid search engine for skill recommendations.
    """
    
    def __init__(self, skills_data_path: str = None):
        """
        Initialize search engine with all components.
        
        Args:
            skills_data_path: Path to skills_raw.jsonl (default: auto-detect)
        """
        # Load skills data
        if skills_data_path is None:
            skills_data_path = get_default_data_path()
        
        print("Loading skills data...")
        self.skills = load_skills(skills_data_path)
        self.skills_by_name = {skill['name']: skill for skill in self.skills}
        
        # Initialize retrievers
        print("\nInitializing BM25 retriever...")
        self.bm25_retriever = BM25Retriever(self.skills)
        
        print("\nInitializing vector retriever...")
        self.vector_retriever = VectorRetriever(self.skills)
        
        print("\nInitializing reranker...")
        self.reranker = Reranker(self.skills)
        
        print("\n" + "="*60)
        print("Search engine ready!")
        print("="*60)
    
    def _merge_results(
        self,
        bm25_results: List[Tuple[str, float]],
        vector_results: List[Tuple[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Merge results from BM25 and vector search (union by skill name).
        Retains both bm25_score and vector_score per candidate.

        Args:
            bm25_results: List of (skill_name, bm25_score) tuples
            vector_results: List of (skill_name, vector_score) tuples

        Returns:
            List of candidate dicts: {"name", "bm25_score", "vector_score"}
            (bm25_score or vector_score may be None if only in one retriever)
        """
        merged = {}
        for name, score in bm25_results:
            merged[name] = {"name": name, "bm25_score": score, "vector_score": None}
        for name, score in vector_results:
            if name in merged:
                merged[name]["vector_score"] = score
            else:
                merged[name] = {"name": name, "bm25_score": None, "vector_score": score}
        return list(merged.values())
    
    def _print_trace(
        self,
        bm25_results: List[Tuple[str, float]],
        vector_results: List[Tuple[str, float]],
        merged_results: List[Dict[str, Any]],
        reranked_results: List[Tuple[str, float, Dict[str, Any]]],
    ) -> None:
        """Print retrieval internals for --trace mode."""
        W = 60
        print("\n" + "=" * W)
        print("TRACE: BM25 top 10")
        print("=" * W)
        for i, (name, score) in enumerate(bm25_results[:10], 1):
            print(f"  {i:2}. {name:<45}  bm25={score:.4f}")

        print("\n" + "=" * W)
        print("TRACE: Vector top 10")
        print("=" * W)
        for i, (name, score) in enumerate(vector_results[:10], 1):
            print(f"  {i:2}. {name:<45}  vec={score:.4f}")

        print("\n" + "=" * W)
        print(f"TRACE: Merged candidates total: {len(merged_results)}")
        print("=" * W)

        print("\n" + "=" * W)
        print("TRACE: Top 10 after rerank")
        print("=" * W)
        for i, (name, final_score, bd) in enumerate(reranked_results[:10], 1):
            print(
                f"  {i:2}. {name:<45}  "
                f"bm25_norm={bd['bm25_norm']:.3f}  "
                f"vec_norm={bd['vector_norm']:.3f}  "
                f"combined={bd['combined_retrieval']:.3f}  "
                f"final={final_score:.4f}"
            )

    def search(
        self,
        query: str,
        top_k: int = 3,
        bm25_top_k: int = 25,
        vector_top_k: int = 25,
        verbose: bool = False,
        trace: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search for skills using hybrid retrieval and reranking.
        
        Args:
            query: Search query string
            top_k: Number of final results to return (default: 3)
            bm25_top_k: Number of results from BM25 (default: 25)
            vector_top_k: Number of results from vector search (default: 25)
            verbose: Print detailed scoring information
            
        Returns:
            List of skill dictionaries with scores, sorted by relevance
        """
        if verbose:
            print(f"\nQuery: '{query}'")
            print("="*60)
        
        # Step 1: BM25 retrieval
        if verbose:
            print(f"\nStep 1: BM25 retrieval (top {bm25_top_k})...")
        bm25_results = self.bm25_retriever.search(query, top_k=bm25_top_k)
        if verbose:
            print(f"  Retrieved {len(bm25_results)} results")
        
        # Step 2: Vector retrieval
        if verbose:
            print(f"\nStep 2: Vector retrieval (top {vector_top_k})...")
        vector_results = self.vector_retriever.search(query, top_k=vector_top_k)
        if verbose:
            print(f"  Retrieved {len(vector_results)} results")
        
        # Step 3: Merge and deduplicate
        if verbose:
            print(f"\nStep 3: Merging results...")
        merged_results = self._merge_results(bm25_results, vector_results)
        if verbose:
            print(f"  Merged to {len(merged_results)} unique skills")
        
        # Step 4: Rerank
        if verbose:
            print(f"\nStep 4: Reranking with custom scoring...")
        reranked_results = self.reranker.rerank(query, merged_results)

        if trace:
            self._print_trace(bm25_results, vector_results, merged_results, reranked_results)

        # Step 5: Get top_k results
        top_results = reranked_results[:top_k]
        
        # Step 6: Build result objects with full skill data
        results = []
        for skill_name, final_score, score_breakdown in top_results:
            skill = self.skills_by_name.get(skill_name)
            if skill:
                result = {
                    'name': skill['name'],
                    'description': skill['description'],
                    'skill_url': skill['skill_url'],
                    'weekly_installs': skill['weekly_installs'],
                    'total_installs': skill['total_installs'],
                    'first_seen': skill['first_seen_str'],
                    'final_score': final_score,
                    'score_breakdown': score_breakdown
                }
                results.append(result)
        
        if verbose:
            print(f"\nFinal top {top_k} results:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['name']}")
                print(f"   Score: {result['final_score']:.4f}")
                print(f"   URL: {result['skill_url']}")
        
        return results
    
    def search_names_only(
        self,
        query: str,
        top_k: int = 3
    ) -> List[str]:
        """
        Search and return only skill names (simplified interface).
        
        Args:
            query: Search query string
            top_k: Number of results to return (default: 3)
            
        Returns:
            List of skill names
        """
        results = self.search(query, top_k=top_k, verbose=False)
        return [r['name'] for r in results]


if __name__ == "__main__":
    # Test the search engine
    print("Initializing search engine...")
    engine = SkillSearchEngine()
    
    # Test queries
    test_queries = [
        "react testing framework",
        "vitest",
        "deployment kubernetes docker",
        "python django",
        "browser automation",
    ]
    
    for query in test_queries:
        print(f"\n\n{'='*80}")
        print(f"QUERY: '{query}'")
        print('='*80)
        
        results = engine.search(query, top_k=3, verbose=False)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['name']}")
            print(f"   Score: {result['final_score']:.4f}")
            print(f"   Description: {result['description'][:150]}...")
            print(f"   Weekly installs: {result['weekly_installs']:,.0f}")
            print(f"   Total installs: {result['total_installs']:,.0f}")
            print(f"   First seen: {result['first_seen']}")
            print(f"   URL: {result['skill_url']}")
            
            # Score breakdown
            breakdown = result['score_breakdown']
            print(f"   Score breakdown:")
            print(f"     - Retrieval: {breakdown['retrieval']:.3f}")
            print(f"     - Title match: {breakdown['title_match']:.3f}")
            print(f"     - Stage 1 score: {breakdown.get('stage1_score', 0):.3f}")
            
            boost_applied = breakdown.get('boost_applied', False)
            if boost_applied:
                print(f"     - Popularity boost: APPLIED ✓")
                print(f"       * Recency: {breakdown['recency']:.3f}")
                print(f"       * Weekly installs: {breakdown['weekly_installs']:.3f}")
                print(f"       * Total installs: {breakdown['total_installs']:.3f}")
            else:
                print(f"     - Popularity boost: NOT APPLIED ✗ (below threshold)")
