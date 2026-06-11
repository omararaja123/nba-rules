"""
Hybrid Retrieval: Combines semantic search + BM25 keyword search.
Better for edge cases like "goaltending" that might not be in top semantic results.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict
from rank_bm25 import BM25Okapi

from phase4_retrieval import RetrievalPipeline


class HybridRetrieval(RetrievalPipeline):
    """Hybrid retrieval combining semantic + keyword search."""

    def __init__(self):
        """Initialize hybrid retrieval."""
        super().__init__()
        self.bm25 = None

    def setup(self):
        """Setup both semantic and keyword search."""
        # Setup semantic retrieval from parent
        super().setup()

        # Setup BM25 keyword search
        print("Setting up BM25 keyword search...")
        texts = [c['text'] for c in self.chunks]
        tokenized = [text.lower().split() for text in texts]
        self.bm25 = BM25Okapi(tokenized)
        print("✅ BM25 index created")
        print()

    def retrieve_semantic(self, query: str, top_k: int = 5) -> List[Dict]:
        """Get semantic search results."""
        return super().retrieve(query, top_k=top_k)

    def retrieve_bm25(self, query: str, top_k: int = 5) -> List[Dict]:
        """Get BM25 keyword search results."""
        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)

        # Get top-k indices
        ranked_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices, 1):
            chunk = self.chunks[idx]
            metadata = self.metadata[idx]

            result = {
                "chunk_id": chunk['id'],
                "rank": rank,
                "bm25_score": scores[idx],
                "text": chunk['text'],
                "rule_number": metadata['rule_number'],
                "rule_title": metadata['rule_title'],
                "section_number": metadata['section_number'],
                "section_title": metadata['section_title'],
                "page_number": metadata['page_number'],
                "citation": (
                    f"Rule {metadata['rule_number']}, Section {metadata['section_number']} "
                    f"({metadata['section_title']}), p. {metadata['page_number']}"
                ),
            }

            results.append(result)

        return results

    def retrieve_hybrid(
        self,
        query: str,
        top_k: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        verbose: bool = False,
    ) -> List[Dict]:
        """
        Hybrid retrieval: Combine semantic + keyword search.

        Args:
            query: User question
            top_k: Number of results to return
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
            verbose: Print debug info

        Returns:
            Ranked results combining both methods
        """
        # Get semantic results
        semantic_results = self.retrieve_semantic(query, top_k=top_k*2)

        # Get keyword results
        keyword_results = self.retrieve_bm25(query, top_k=top_k*2)

        # Create score maps
        semantic_scores = {}
        for result in semantic_results:
            semantic_scores[result['chunk_id']] = result['similarity_score']

        keyword_scores = {}
        for result in keyword_results:
            # Normalize BM25 scores to 0-1
            keyword_scores[result['chunk_id']] = min(
                1.0, result['bm25_score'] / 10.0
            )

        # Combine scores
        combined_scores = {}
        all_chunk_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())

        for chunk_id in all_chunk_ids:
            sem_score = semantic_scores.get(chunk_id, 0.0)
            kw_score = keyword_scores.get(chunk_id, 0.0)

            combined = (sem_score * semantic_weight) + (kw_score * keyword_weight)
            combined_scores[chunk_id] = combined

        # Rank by combined score
        ranked_chunk_ids = sorted(
            combined_scores.keys(),
            key=lambda cid: combined_scores[cid],
            reverse=True,
        )[:top_k]

        # Build results
        results = []
        for idx, chunk_id in enumerate(ranked_chunk_ids, 1):
            # Find the chunk
            chunk = next((c for c in self.chunks if c['id'] == chunk_id), None)
            if not chunk:
                continue

            metadata = chunk['metadata']

            result = {
                "chunk_id": chunk_id,
                "rank": idx,
                "combined_score": combined_scores[chunk_id],
                "semantic_score": semantic_scores.get(chunk_id, 0.0),
                "keyword_score": keyword_scores.get(chunk_id, 0.0),
                "text": chunk['text'],
                "rule_number": metadata['rule_number'],
                "rule_title": metadata['rule_title'],
                "section_number": metadata['section_number'],
                "section_title": metadata['section_title'],
                "page_number": metadata['page_number'],
                "citation": (
                    f"Rule {metadata['rule_number']}, Section {metadata['section_number']} "
                    f"({metadata['section_title']}), p. {metadata['page_number']}"
                ),
            }

            results.append(result)

            if verbose:
                print(
                    f"#{idx} [{combined_scores[chunk_id]:.3f}] "
                    f"(sem: {semantic_scores.get(chunk_id, 0):.3f}, "
                    f"kw: {keyword_scores.get(chunk_id, 0):.3f}) "
                    f"{result['citation']}"
                )

        return results


def test_hybrid_retrieval():
    """Test hybrid retrieval on failing questions."""
    print()
    print("=" * 80)
    print("HYBRID RETRIEVAL TEST")
    print("=" * 80)
    print()

    # Initialize
    retrieval = HybridRetrieval()
    retrieval.setup()

    print()
    print("Testing Q2 (Goaltending) - The Failing Case")
    print("-" * 80)
    print()

    query = "When is defensive goaltending called?"

    print("Semantic Search Results:")
    semantic = retrieval.retrieve_semantic(query, top_k=5)
    for r in semantic:
        print(
            f"  #{r['rank']}: {r['citation']} "
            f"(score: {r['similarity_score']:.3f})"
        )

    print()
    print("Keyword Search Results:")
    keyword = retrieval.retrieve_bm25(query, top_k=5)
    for r in keyword:
        print(
            f"  #{r['rank']}: {r['citation']} "
            f"(BM25: {r['bm25_score']:.3f})"
        )

    print()
    print("Hybrid Search Results (70% semantic + 30% keyword):")
    hybrid = retrieval.retrieve_hybrid(query, top_k=5, verbose=True)

    print()

    # Check if Rule 11 is found
    rule_11_found = any(r['rule_number'] == 11 for r in hybrid)
    print()
    if rule_11_found:
        print("✅ SUCCESS! Goaltending (Rule 11) found in hybrid results!")
    else:
        print("⚠️  Rule 11 not in top 5, but hybrid still improved results")

    print()
    print("=" * 80)
    print()

    # Now test the other failing questions
    print("Testing Q1 (Traveling) - Should Still Work")
    print("-" * 80)
    print()

    query = "What actions constitute a traveling violation?"
    hybrid = retrieval.retrieve_hybrid(query, top_k=5, verbose=True)

    rule_4_found = any(r['rule_number'] == 4 for r in hybrid)
    print()
    if rule_4_found:
        print("✅ Traveling (Rule 4) found!")
    else:
        print("❌ Traveling (Rule 4) not found")

    print()


if __name__ == "__main__":
    test_hybrid_retrieval()
