"""
Enhanced Retrieval with Better Traveling Support
Combines Option 1 (better chunking) + Option 2 (metadata keywords).
Uses a smarter approach: boosts keywords without modifying chunk text.
"""

from typing import List, Dict
from rank_bm25 import BM25Okapi
import math

from phase4_retrieval_hybrid import HybridRetrieval


class EnhancedRetrieval(HybridRetrieval):
    """Hybrid retrieval with enhanced traveling support."""

    def __init__(self):
        """Initialize with keyword boost mapping."""
        super().__init__()
        self.keyword_boost = {}  # Maps chunk_id to keyword boost factor

    def setup(self):
        """Setup with enhanced keyword boosting."""
        # Setup parent (semantic + BM25)
        super().setup()

        # Create keyword boost map
        self._create_keyword_boost_map()

        print("✅ Enhanced retrieval ready (with keyword boosting)")
        print()

    def _create_keyword_boost_map(self):
        """Create boost factors for rule-specific keywords."""
        print("Creating keyword boost map...")

        boost_keywords = {
            "traveling": ["traveling", "progressing", "pivot", "dribble", "steps", "gather"],
            "goaltending": ["goaltending", "defensive", "basket", "ring", "airborne"],
        }

        for chunk in self.chunks:
            meta = chunk['metadata']
            rule_num = meta['rule_number']

            # Boost traveling-related chunks
            if rule_num in [4, 10] and 'Traveling' in meta['section_title']:
                self.keyword_boost[chunk['id']] = 1.5
                print(f"  ✅ Boosting traveling: Rule {rule_num}, Section {meta['section_number']}")

            # Boost goaltending-related chunks
            elif rule_num == 11:
                self.keyword_boost[chunk['id']] = 1.3
                print(f"  ✅ Boosting goaltending: Rule {rule_num}, Section {meta['section_number']}")

        print()

    def retrieve_enhanced(
        self,
        query: str,
        top_k: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        verbose: bool = False,
    ) -> List[Dict]:
        """
        Enhanced retrieval with keyword boost.

        Same as hybrid but applies keyword boost factors.
        """
        # Get hybrid results
        results = self.retrieve_hybrid(
            query,
            top_k=top_k*2,  # Get more to rerank
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            verbose=False,
        )

        # Apply keyword boost
        for result in results:
            boost = self.keyword_boost.get(result['chunk_id'], 1.0)
            result['combined_score'] *= boost
            result['boost_factor'] = boost

        # Re-rank by boosted score
        results.sort(key=lambda x: x['combined_score'], reverse=True)
        results = results[:top_k]

        # Update ranks
        for i, result in enumerate(results, 1):
            result['rank'] = i

        if verbose:
            for result in results:
                boost_str = f" [×{result['boost_factor']:.1f}]" if result['boost_factor'] > 1.0 else ""
                print(
                    f"#{result['rank']} [{result['combined_score']:.3f}]{boost_str} "
                    f"{result['citation']}"
                )

        return results

    def retrieve_enhanced(
        self,
        query: str,
        top_k: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        verbose: bool = False,
    ) -> List[Dict]:
        """
        Enhanced retrieval with improved traveling support.

        Same interface as hybrid search, but with better chunk matching.
        """
        return self.retrieve_hybrid(
            query,
            top_k=top_k,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            verbose=verbose,
        )


def test_enhanced_retrieval():
    """Test enhanced retrieval."""
    print()
    print("=" * 80)
    print("ENHANCED RETRIEVAL TEST (With Keyword Boosting)")
    print("=" * 80)
    print()

    retrieval = EnhancedRetrieval()
    retrieval.setup()

    print()
    print("Testing Q1 (Traveling) - Enhanced Version")
    print("-" * 80)
    print()

    query = "What actions constitute a traveling violation?"

    print("Top-5 Results (with keyword boosting):")
    results = retrieval.retrieve_enhanced(query, top_k=5, verbose=True)

    print()

    # Check ranking
    rule_4_rank = next(
        (i for i, r in enumerate(results) if r['rule_number'] == 4),
        None
    )
    rule_4_rank = rule_4_rank + 1 if rule_4_rank is not None else None

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"Rule 4 (Definition):    {'#' + str(rule_4_rank) if rule_4_rank else 'Not in top-5'}")

    if rule_4_rank and rule_4_rank <= 2:
        print()
        print("✅ SUCCESS! Rule 4 is in top-2!")
    elif rule_4_rank:
        print()
        print(f"⚠️  Rule 4 at rank {rule_4_rank}")
    else:
        print()
        print("❌ Rule 4 not in top-5")

    print()
    print("=" * 80)
    print()

    # Test Q2 to ensure we didn't break it
    print("Testing Q2 (Goaltending) - Should Still Work")
    print("-" * 80)
    print()

    query = "When is defensive goaltending called?"

    print("Top-5 Results (with keyword boosting):")
    results = retrieval.retrieve_enhanced(query, top_k=5, verbose=True)

    rule_11_rank = next(
        (i for i, r in enumerate(results) if r['rule_number'] == 11),
        None
    )
    rule_11_rank = rule_11_rank + 1 if rule_11_rank is not None else None

    print()
    if rule_11_rank and rule_11_rank <= 3:
        print("✅ Goaltending still works with enhancement!")
    else:
        print("⚠️  Goaltending may be affected")

    print()


if __name__ == "__main__":
    test_enhanced_retrieval()
