"""
Reranker with custom scoring.

Combines retrieval scores with additional signals:
- Title match bonus
- Recency score
- Weekly installs
- Total installs
"""

import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Tuple


class Reranker:
    """
    Two-stage reranker with relevance threshold.
    
    Stage 1: Rank by retrieval + title match
    Stage 2: Apply recency/installs boost only to highly relevant results
    """
    
    def __init__(
        self,
        skills: List[Dict[str, Any]],
        retrieval_weight: float = 0.5,
        title_match_weight: float = 0.1,
        recency_weight: float = 0.15,
        weekly_installs_weight: float = 0.15,
        total_installs_weight: float = 0.1,
        relevance_threshold: float = 0.4
    ):
        """
        Initialize reranker with scoring weights.
        
        Args:
            skills: List of all skill dictionaries
            retrieval_weight: Weight for BM25/vector retrieval score (default: 50%)
            title_match_weight: Weight for title match bonus (default: 10%)
            recency_weight: Weight for recency score (default: 15%)
            weekly_installs_weight: Weight for weekly installs (default: 15%)
            total_installs_weight: Weight for total installs (default: 10%)
            relevance_threshold: Minimum retrieval score to apply install/recency boost
        """
        self.skills = skills
        self.skills_by_name = {skill['name']: skill for skill in skills}
        
        # Scoring weights
        self.retrieval_weight = retrieval_weight
        self.title_match_weight = title_match_weight
        self.recency_weight = recency_weight
        self.weekly_installs_weight = weekly_installs_weight
        self.total_installs_weight = total_installs_weight
        self.relevance_threshold = relevance_threshold
        
        # Pre-compute normalization factors
        self._compute_normalization_factors()
    
    def _compute_normalization_factors(self):
        """
        Compute min/max values for normalization.
        """
        weekly_installs = [s['weekly_installs'] for s in self.skills]
        total_installs = [s['total_installs'] for s in self.skills]
        
        # Use log scale for installs (to handle large ranges)
        self.weekly_log_values = [np.log1p(x) for x in weekly_installs]
        self.total_log_values = [np.log1p(x) for x in total_installs]
        
        self.weekly_log_min = min(self.weekly_log_values) if self.weekly_log_values else 0
        self.weekly_log_max = max(self.weekly_log_values) if self.weekly_log_values else 1
        
        self.total_log_min = min(self.total_log_values) if self.total_log_values else 0
        self.total_log_max = max(self.total_log_values) if self.total_log_values else 1
        
        # Avoid division by zero
        self.weekly_log_range = max(self.weekly_log_max - self.weekly_log_min, 1e-6)
        self.total_log_range = max(self.total_log_max - self.total_log_min, 1e-6)
    
    def _normalize_retrieval_score(
        self, 
        scores: List[Tuple[str, float]]
    ) -> Dict[str, float]:
        """
        Normalize retrieval scores to [0, 1] range.
        
        Args:
            scores: List of (skill_name, score) tuples
            
        Returns:
            Dictionary mapping skill_name to normalized score
        """
        if not scores:
            return {}
        
        score_values = [s[1] for s in scores]
        min_score = min(score_values)
        max_score = max(score_values)
        score_range = max(max_score - min_score, 1e-6)
        
        normalized = {}
        for name, score in scores:
            normalized[name] = (score - min_score) / score_range
        
        return normalized
    
    def _compute_title_match_score(self, query: str, skill_name: str) -> float:
        """
        Compute title match score.
        
        Args:
            query: Search query
            skill_name: Skill name
            
        Returns:
            Score: 1.0 for exact match, 0.5 for partial match, 0.0 for no match
        """
        query_lower = query.lower().strip()
        name_lower = skill_name.lower().strip()
        
        # Exact match
        if query_lower == name_lower:
            return 1.0
        
        # Check if query is in name or name is in query
        if query_lower in name_lower or name_lower in query_lower:
            return 0.5
        
        # Check for word-level matches
        query_words = set(query_lower.split())
        name_words = set(name_lower.split())
        
        if query_words & name_words:  # Intersection
            overlap_ratio = len(query_words & name_words) / max(len(query_words), 1)
            return 0.3 * overlap_ratio
        
        return 0.0
    
    def _compute_recency_score(self, first_seen: datetime) -> float:
        """
        Compute recency score with exponential decay.
        
        Args:
            first_seen: Date when skill was first seen
            
        Returns:
            Score in [0, 1] range, higher for more recent skills
        """
        now = datetime.now()
        days_old = (now - first_seen).days
        
        # Exponential decay: 1 / (1 + days / 30)
        # Skills from last 30 days get high scores
        score = 1.0 / (1.0 + days_old / 30.0)
        
        return score
    
    def _compute_installs_score(
        self, 
        installs: float, 
        log_min: float, 
        log_max: float, 
        log_range: float
    ) -> float:
        """
        Compute normalized install score using log scale.
        
        Args:
            installs: Number of installs
            log_min: Minimum log value
            log_max: Maximum log value
            log_range: Range of log values
            
        Returns:
            Normalized score in [0, 1] range
        """
        if installs <= 0:
            return 0.0
        
        log_value = np.log1p(installs)
        normalized = (log_value - log_min) / log_range
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, normalized))
    
    def rerank(
        self, 
        query: str, 
        candidates: List[Tuple[str, float]],
        top_n_for_stage2: int = 50
    ) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Two-stage reranking with relevance threshold.
        
        Stage 1: Rank by retrieval + title match, take top N
        Stage 2: Within top N, apply recency/installs boost only if retrieval >= threshold
        
        Args:
            query: Search query
            candidates: List of (skill_name, retrieval_score) tuples
            top_n_for_stage2: Number of top results to keep for stage 2 refinement
            
        Returns:
            List of (skill_name, final_score, score_breakdown) tuples,
            sorted by final_score descending
        """
        # Normalize retrieval scores
        normalized_retrieval = self._normalize_retrieval_score(candidates)
        
        # Stage 1: Compute base scores (retrieval + title)
        stage1_results = []
        
        for skill_name, raw_retrieval_score in candidates:
            skill = self.skills_by_name.get(skill_name)
            if not skill:
                continue
            
            # Get normalized retrieval score
            retrieval_score = normalized_retrieval.get(skill_name, 0.0)
            
            # Compute title match
            title_match_score = self._compute_title_match_score(query, skill_name)
            
            # Stage 1 score: only retrieval + title
            stage1_score = (
                retrieval_score * self.retrieval_weight +
                title_match_score * self.title_match_weight
            )
            
            stage1_results.append({
                'name': skill_name,
                'retrieval_score': retrieval_score,
                'title_match_score': title_match_score,
                'stage1_score': stage1_score,
                'skill': skill
            })
        
        # Sort by stage1 score and take top N
        stage1_results.sort(key=lambda x: x['stage1_score'], reverse=True)
        top_n_candidates = stage1_results[:top_n_for_stage2]
        
        # Stage 2: Apply recency/installs boost with threshold
        final_results = []
        
        for candidate in top_n_candidates:
            skill_name = candidate['name']
            skill = candidate['skill']
            retrieval_score = candidate['retrieval_score']
            title_match_score = candidate['title_match_score']
            stage1_score = candidate['stage1_score']
            
            # Compute recency and installs scores
            recency_score = self._compute_recency_score(skill['first_seen'])
            
            weekly_installs_score = self._compute_installs_score(
                skill['weekly_installs'],
                self.weekly_log_min,
                self.weekly_log_max,
                self.weekly_log_range
            )
            
            total_installs_score = self._compute_installs_score(
                skill['total_installs'],
                self.total_log_min,
                self.total_log_max,
                self.total_log_range
            )
            
            # Apply threshold: only add installs boost if retrieval >= threshold
            if retrieval_score >= self.relevance_threshold:
                final_score = (
                    stage1_score +
                    recency_score * self.recency_weight +
                    weekly_installs_score * self.weekly_installs_weight +
                    total_installs_score * self.total_installs_weight
                )
                boost_applied = True
            else:
                # Below threshold: only use stage1 score (retrieval + title)
                final_score = stage1_score
                boost_applied = False
            
            # Store score breakdown for debugging
            score_breakdown = {
                'retrieval': retrieval_score,
                'title_match': title_match_score,
                'recency': recency_score,
                'weekly_installs': weekly_installs_score,
                'total_installs': total_installs_score,
                'boost_applied': boost_applied,
                'stage1_score': stage1_score
            }
            
            final_results.append((skill_name, final_score, score_breakdown))
        
        # Sort by final score descending
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        return final_results


if __name__ == "__main__":
    # Test the reranker
    from data_loader import load_skills, get_default_data_path
    
    print("Loading skills...")
    skills = load_skills(get_default_data_path())
    
    print("\nInitializing reranker...")
    reranker = Reranker(skills)
    
    # Mock candidates
    query = "react testing"
    candidates = [
        ("vitest", 0.85),
        ("react-testing-library", 0.75),
        ("jest", 0.70),
        ("cypress", 0.65),
        ("playwright", 0.60)
    ]
    
    print(f"\nReranking candidates for query: '{query}'")
    print(f"{'='*80}")
    
    results = reranker.rerank(query, candidates)
    
    for i, (name, score, breakdown) in enumerate(results[:5], 1):
        print(f"\n{i}. {name} (final score: {score:.4f})")
        print(f"   Retrieval: {breakdown['retrieval']:.3f} | "
              f"Title: {breakdown['title_match']:.3f} | "
              f"Recency: {breakdown['recency']:.3f}")
        print(f"   Weekly: {breakdown['weekly_installs']:.3f} | "
              f"Total: {breakdown['total_installs']:.3f}")
