"""
Vector retriever for semantic search.

Uses sentence-transformers when available; falls back to TF-IDF vectors otherwise.
Includes embedding caching for performance.
"""

import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    from sentence_transformers import SentenceTransformer
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    SentenceTransformer = None
    _HAS_SENTENCE_TRANSFORMERS = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class VectorRetriever:
    """
    Semantic vector retriever using sentence transformers.
    """
    
    def __init__(
        self, 
        skills: List[Dict[str, Any]], 
        model_name: str = 'all-MiniLM-L6-v2',
        cache_path: str = None
    ):
        """
        Initialize vector retriever with skill documents.
        
        Args:
            skills: List of skill dictionaries
            model_name: Name of sentence-transformer model to use
            cache_path: Path to cache embeddings (default: search/embeddings_cache.pkl)
        """
        self.skills = skills
        self.skill_names = [skill['name'] for skill in skills]
        self.model_name = model_name
        
        # Set cache path
        if cache_path is None:
            cache_dir = Path(__file__).parent
            self.cache_path = cache_dir / "embeddings_cache.pkl"
        else:
            self.cache_path = Path(cache_path)
        
        # Load or create embeddings
        self.embeddings = self._load_or_create_embeddings()
    
    def _get_embedding_texts(self) -> List[str]:
        """
        Get texts to embed (name + description for each skill).
        
        Returns:
            List of texts to embed
        """
        texts = []
        for skill in self.skills:
            # Combine name and description for embedding
            # Name is more important, so we put it first
            text = f"{skill['name']}. {skill['description']}"
            texts.append(text)
        return texts
    
    def _create_cache_key(self) -> str:
        """
        Create a cache key based on model and data.
        
        Returns:
            Cache key string
        """
        backend = "st" if _HAS_SENTENCE_TRANSFORMERS else "tfidf"
        return f"{backend}_{self.model_name}_{len(self.skills)}"
    
    def _load_or_create_embeddings(self) -> np.ndarray:
        """
        Load embeddings from cache or create new ones.
        Uses sentence-transformers when available, else TF-IDF.
        
        Returns:
            NumPy array of embeddings (shape: [num_skills, embedding_dim])
        """
        cache_key = self._create_cache_key()
        
        # Try to load from cache
        if self.cache_path.exists():
            try:
                print(f"Loading embeddings from cache: {self.cache_path}")
                with open(self.cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                
                # Check if cache is valid
                if cached_data.get('cache_key') == cache_key:
                    embeddings = cached_data['embeddings']
                    self._tfidf_vectorizer = cached_data.get('tfidf_vectorizer')
                    print(f"Loaded {embeddings.shape[0]} embeddings from cache")
                    return embeddings
                else:
                    print("Cache key mismatch, regenerating embeddings...")
            except Exception as e:
                print(f"Failed to load cache: {e}")
        
        texts = self._get_embedding_texts()
        
        if _HAS_SENTENCE_TRANSFORMERS:
            # Create new embeddings with sentence-transformers
            print(f"Creating embeddings using model: {self.model_name}")
            print("This may take a few minutes for the first run...")
            model = SentenceTransformer(self.model_name)
            embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
            self._tfidf_vectorizer = None
        else:
            # Fallback: TF-IDF vectors (no torch/sentence-transformers required)
            print("Using TF-IDF fallback (sentence-transformers not available)")
            vectorizer = TfidfVectorizer(max_features=384, stop_words="english", ngram_range=(1, 2))
            embeddings = vectorizer.fit_transform(texts).toarray().astype(np.float32)
            self._tfidf_vectorizer = vectorizer  # for query encoding in search()
        
        # Save to cache
        try:
            print(f"Saving embeddings to cache: {self.cache_path}")
            cache_data = {
                'cache_key': cache_key,
                'embeddings': embeddings,
                'model_name': self.model_name
            }
            if self._tfidf_vectorizer is not None:
                cache_data['tfidf_vectorizer'] = self._tfidf_vectorizer
            with open(self.cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            print("Embeddings cached successfully")
        except Exception as e:
            print(f"Warning: Failed to cache embeddings: {e}")
        
        return embeddings
    
    def search(self, query: str, top_k: int = 25) -> List[Tuple[str, float]]:
        """
        Search for skills using semantic similarity.
        
        Args:
            query: Search query string
            top_k: Number of top results to return (default: 25)
            
        Returns:
            List of (skill_name, similarity_score) tuples, sorted by score descending
        """
        if getattr(self, '_tfidf_vectorizer', None) is not None:
            # TF-IDF path: encode query with same vectorizer
            query_vec = self._tfidf_vectorizer.transform([query]).toarray().astype(np.float32)
        else:
            # sentence-transformers path
            model = SentenceTransformer(self.model_name)
            query_vec = model.encode([query], convert_to_numpy=True)
        
        # Compute cosine similarities
        similarities = cosine_similarity(query_vec, self.embeddings)[0]
        
        # Create (name, score) pairs
        results = list(zip(self.skill_names, similarities))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return results[:top_k]
    
    def get_skill_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get full skill data by name.
        
        Args:
            name: Skill name
            
        Returns:
            Skill dictionary
        """
        for skill in self.skills:
            if skill['name'] == name:
                return skill
        return None


if __name__ == "__main__":
    # Test the vector retriever
    from data_loader import load_skills, get_default_data_path
    
    print("Loading skills...")
    skills = load_skills(get_default_data_path())
    
    print("\nInitializing vector retriever...")
    retriever = VectorRetriever(skills)
    
    # Test queries
    test_queries = [
        "react performance optimization",
        "testing framework",
        "deploy containers",
        "database queries"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print(f"{'='*60}")
        
        results = retriever.search(query, top_k=5)
        
        for i, (name, score) in enumerate(results, 1):
            print(f"{i}. {name:<40} (similarity: {score:.4f})")
