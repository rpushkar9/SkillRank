"""
BM25 retriever for keyword-based search.

Uses the rank_bm25 library to perform efficient BM25 scoring on skill documents.
"""

import re
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi

# Use NLTK stopwords
import nltk

# Download required NLTK data if not present
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)

from nltk.corpus import stopwords
STOPWORDS = set(stopwords.words('english'))


def tokenize(text: str) -> List[str]:
    """
    Tokenize text for BM25 indexing.

    Steps:
    1. Lowercase and extract alphanumeric tokens, removing stopwords and
       single-character tokens.
    2. Append concatenated bigrams for every pair of adjacent tokens so that
       hyphenated or spaced compound terms ("front-end", "front end",
       "frontend") all produce the same "frontend" token and match each other.

    Args:
        text: Text to tokenize

    Returns:
        List of tokens (unigrams + adjacent concatenated bigrams)
    """
    # Convert to lowercase
    text = text.lower()

    # Split on non-alphanumeric characters
    tokens = re.findall(r'\b[a-z0-9]+\b', text)

    # Remove stopwords and very short tokens
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    # Append concatenated bigrams for adjacent token pairs so that
    # "front" + "end" → "frontend", "node" + "js" → "nodejs", etc.
    # This makes "frontend", "front-end", and "front end" all match.
    bigrams = [tokens[i] + tokens[i + 1] for i in range(len(tokens) - 1)]
    tokens = tokens + bigrams

    return tokens


class BM25Retriever:
    """
    BM25-based keyword retriever for skills.
    """
    
    def __init__(self, skills: List[Dict[str, Any]]):
        """
        Initialize BM25 retriever with skill documents.
        
        Args:
            skills: List of skill dictionaries with 'searchable_text' field
        """
        self.skills = skills
        self.skill_names = [skill['name'] for skill in skills]
        
        # Tokenize all documents
        print("Tokenizing documents for BM25...")
        self.tokenized_corpus = [
            tokenize(skill['searchable_text']) for skill in skills
        ]
        
        # Build BM25 index
        print("Building BM25 index...")
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"BM25 index built with {len(self.skills)} documents")
    
    def search(self, query: str, top_k: int = 25) -> List[Tuple[str, float]]:
        """
        Search for skills using BM25 scoring.
        
        Args:
            query: Search query string
            top_k: Number of top results to return (default: 25)
            
        Returns:
            List of (skill_name, bm25_score) tuples, sorted by score descending
        """
        # Tokenize query
        query_tokens = tokenize(query)
        
        if not query_tokens:
            return []
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Create (name, score) pairs
        results = list(zip(self.skill_names, scores))
        
        # Sort by score descending
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
    # Test the BM25 retriever
    from data_loader import load_skills, get_default_data_path
    
    print("Loading skills...")
    skills = load_skills(get_default_data_path())
    
    print("\nInitializing BM25 retriever...")
    retriever = BM25Retriever(skills)
    
    # Test queries
    test_queries = [
        "react testing",
        "vitest",
        "deployment kubernetes",
        "python django"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print(f"{'='*60}")
        
        results = retriever.search(query, top_k=5)
        
        for i, (name, score) in enumerate(results, 1):
            print(f"{i}. {name:<40} (score: {score:.4f})")
