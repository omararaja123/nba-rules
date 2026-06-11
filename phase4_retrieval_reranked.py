"""
Reranking: Hybrid Retrieval + Cross-Encoder Reranker
Improves retrieval by re-scoring chunks using a domain-aware model.
"""

from typing import List, Dict
from sentence_transformers import CrossEncoder

from phase4_retrieval_hybrid import HybridRetrieval


class RerankedRetrieval(HybridRetrieval):
    """Hybrid retrieval with cross-encoder reranking."""

    def __init__(self):
        """Initialize reranked retrieval."""
        super().__init__()
        self.reranker = None

    def setup(self):
        """Setup retrieval + reranker."""
        # Setup hybrid retrieval
        super().setup()

        # Setup cross-encoder reranker
        print("Setting up Cross-Encoder reranker...")
        print("  Model: cross-encoder/ms-marco-MiniLM-L-6-v2")
        print("  Purpose: Retrieval ranking (trained on MS MARCO)")
        self.reranker = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            max_length=512
        )
        print("✅ Reranker loaded")
        print()

    def retrieve_with_reranking(
        self,
        query: str,
        top_k: int = 5,
        rerank_top_k: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        verbose: bool = False,
    ) -> List[Dict]:
        """
        Retrieve with hybrid search + reranking.

        Args:
            query: User question
            top_k: Final number of results to return
            rerank_top_k: Number of candidates to rerank
            semantic_weight: Weight for semantic search
            keyword_weight: Weight for keyword search
            verbose: Print debug info

        Returns:
            Reranked results
        """
        # Step 1: Hybrid retrieval (get more candidates than needed)
        hybrid_results = self.retrieve_hybrid(
            query,
            top_k=rerank_top_k,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            verbose=False,
        )

        if not hybrid_results:
            return []

        # Step 2: Prepare for reranking
        # CrossEncoder expects pairs: (query, document_text)
        pairs = []
        for result in hybrid_results:
            pairs.append([query, result['text']])

        # Step 3: Rerank using cross-encoder
        reranker_scores = self.reranker.predict(pairs)

        # Step 4: Combine scores
        # Blend hybrid score (0.7) with reranker score (0.3)
        combined_results = []
        for i, result in enumerate(hybrid_results):
            # Normalize reranker score to 0-1 (it's usually -3 to +3)
            # We'll use sigmoid: 1 / (1 + exp(-x))
            import math
            reranker_normalized = 1.0 / (1.0 + math.exp(-reranker_scores[i]))

            # Blend: favor hybrid but give reranker influence
            final_score = (result['combined_score'] * 0.7) + (reranker_normalized * 0.3)

            result['reranker_score'] = reranker_normalized
            result['final_score'] = final_score
            combined_results.append(result)

        # Step 5: Re-rank by final score
        combined_results.sort(key=lambda x: x['final_score'], reverse=True)

        # Step 6: Return top-k
        final_results = combined_results[:top_k]

        if verbose:
            for i, result in enumerate(final_results, 1):
                print(
                    f"#{i} [{result['final_score']:.3f}] "
                    f"(hybrid: {result['combined_score']:.3f}, "
                    f"rerank: {result['reranker_score']:.3f}) "
                    f"{result['citation']}"
                )

        return final_results


def test_reranker():
    """Test reranker on failing questions."""
    print()
    print("=" * 80)
    print("RERANKER TEST")
    print("=" * 80)
    print()

    retrieval = RerankedRetrieval()
    retrieval.setup()

    print()
    print("Testing Q1 (Traveling) - The Challenge Case")
    print("-" * 80)
    print()

    query = "What actions constitute a traveling violation?"

    print("Hybrid Search (Before Reranking):")
    hybrid = retrieval.retrieve_hybrid(query, top_k=5, verbose=True)
    print()

    print("With Cross-Encoder Reranking (After):")
    reranked = retrieval.retrieve_with_reranking(
        query, top_k=5, rerank_top_k=10, verbose=True
    )

    print()

    # Check if Rule 4 improved
    hybrid_rule_4_rank = next(
        (i + 1 for i, r in enumerate(hybrid) if r['rule_number'] == 4),
        None
    )
    reranked_rule_4_rank = next(
        (i + 1 for i, r in enumerate(reranked) if r['rule_number'] == 4),
        None
    )

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"Traveling (Rule 4) Rank:")
    print(f"  Hybrid: #{hybrid_rule_4_rank if hybrid_rule_4_rank else 'Not in top-5'}")
    print(f"  Reranked: #{reranked_rule_4_rank if reranked_rule_4_rank else 'Not in top-5'}")

    if reranked_rule_4_rank and (not hybrid_rule_4_rank or reranked_rule_4_rank < hybrid_rule_4_rank):
        print()
        print("✅ SUCCESS! Reranker moved Rule 4 up!")
    else:
        print()
        print("⚠️  Reranker didn't improve traveling ranking (still challenging)")

    print()
    print("=" * 80)
    print()

    # Now test Q2 (should stay good)
    print("Testing Q2 (Goaltending) - Should Stay Perfect")
    print("-" * 80)
    print()

    query = "When is defensive goaltending called?"

    print("With Cross-Encoder Reranking:")
    reranked = retrieval.retrieve_with_reranking(
        query, top_k=5, rerank_top_k=10, verbose=True
    )

    rule_11_found = any(r['rule_number'] == 11 for r in reranked)
    print()
    if rule_11_found:
        print("✅ Goaltending still works with reranker!")
    else:
        print("❌ Reranker broke goaltending (not good)")

    print()


if __name__ == "__main__":
    test_reranker()
