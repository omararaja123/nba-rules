"""
Phase 4: Parent-Child Hybrid Retrieval with Cross-Encoder Re-ranking
Advanced RAG architecture for maximum relevance.
"""

import json
import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import faiss


class ParentChildRetrieval:
    """Parent-Child Hybrid Retrieval with Cross-Encoder Re-ranking."""

    def __init__(self):
        """Initialize parent-child retrieval system."""
        self.child_chunks = []
        self.parent_chunks = []
        self.child_parent_mapping = {}
        self.child_embeddings = None
        self.parent_embeddings = None
        self.child_index = None
        self.parent_index = None
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.reranker = None

    def setup(self):
        """Setup parent-child retrieval system."""
        print("=" * 80)
        print("SETTING UP PARENT-CHILD HYBRID RETRIEVAL")
        print("=" * 80)
        print()

        # Load child chunks
        print("Loading child chunks...")
        with open('data/09_stable_chunks.json', 'r') as f:
            data = json.load(f)
        self.child_chunks = data['chunks']
        print(f"✅ Loaded {len(self.child_chunks)} child chunks")
        print()

        # Load parent chunks
        print("Loading parent chunks...")
        with open('data/11_parent_chunks.json', 'r') as f:
            data = json.load(f)
        self.parent_chunks = data['chunks']
        print(f"✅ Loaded {len(self.parent_chunks)} parent chunks")
        print()

        # Load child-parent mapping
        print("Loading child-parent mapping...")
        with open('data/11_child_parent_mapping.json', 'r') as f:
            self.child_parent_mapping = json.load(f)
        print(f"✅ Loaded mapping for {len(self.child_parent_mapping)} chunks")
        print()

        # Load embeddings
        print("Loading embeddings...")
        self.child_embeddings = np.load('data/10_embeddings.npy')
        self.parent_embeddings = np.load('data/11_parent_embeddings.npy')
        print(f"✅ Child embeddings: {self.child_embeddings.shape}")
        print(f"✅ Parent embeddings: {self.parent_embeddings.shape}")
        print()

        # Build FAISS indices
        print("Building FAISS indices...")
        child_dim = self.child_embeddings.shape[1]
        self.child_index = faiss.IndexFlatL2(child_dim)
        self.child_index.add(self.child_embeddings.astype(np.float32))

        parent_dim = self.parent_embeddings.shape[1]
        self.parent_index = faiss.IndexFlatL2(parent_dim)
        self.parent_index.add(self.parent_embeddings.astype(np.float32))
        print("✅ FAISS indices created")
        print()

        # Build BM25
        print("Building BM25 indices...")
        child_texts = [c['text'] for c in self.child_chunks]
        child_tokenized = [text.lower().split() for text in child_texts]
        self.child_bm25 = BM25Okapi(child_tokenized)

        parent_texts = [p['text'] for p in self.parent_chunks]
        parent_tokenized = [text.lower().split() for text in parent_texts]
        self.parent_bm25 = BM25Okapi(parent_tokenized)
        print("✅ BM25 indices created")
        print()

        # Load cross-encoder for re-ranking
        print("Loading cross-encoder for re-ranking...")
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print("✅ Cross-encoder loaded")
        print()

    def retrieve_parent_child(
        self,
        query: str,
        top_k_children: int = 10,
        top_k_parents: int = 5,
        verbose: bool = False,
    ) -> List[Dict]:
        """
        Retrieve using parent-child architecture.

        1. Search child chunks with hybrid (semantic + keyword)
        2. Expand to get parent chunks
        3. Re-rank parent chunks with cross-encoder
        4. Return top parent chunks
        """

        # Step 1: Encode query
        query_embedding = self.encoder.encode(query)

        # Step 2: Hybrid search on child chunks
        distances, child_indices = self.child_index.search(
            np.array([query_embedding]).astype(np.float32), top_k_children
        )

        # BM25 on children
        tokens = query.lower().split()
        child_bm25_scores = self.child_bm25.get_scores(tokens)

        # Combine scores for children
        child_scores = {}
        for j, idx in enumerate(child_indices[0]):
            sim_score = 1.0 / (1.0 + distances[0][j])
            bm25_score = min(1.0, child_bm25_scores[idx] / 10.0)
            combined = (sim_score * 0.7) + (bm25_score * 0.3)
            child_scores[idx] = combined

        if verbose:
            print(f"Top child chunks by hybrid score:")
            for idx, score in sorted(child_scores.items(), key=lambda x: x[1], reverse=True)[:5]:
                chunk = self.child_chunks[idx]
                print(f"  {chunk['id']}: {score:.3f}")

        # Step 3: Expand to parent chunks
        parent_ids_with_children = set()
        for child_idx in child_scores.keys():
            child_id = self.child_chunks[child_idx]['id']
            if child_id in self.child_parent_mapping:
                parent_id = self.child_parent_mapping[child_id]['parent_id']
                parent_ids_with_children.add(parent_id)

        # Find parent chunks by ID
        parent_results = {}
        for parent in self.parent_chunks:
            if parent['id'] in parent_ids_with_children:
                parent_results[parent['id']] = {
                    'chunk': parent,
                    'rule': parent['metadata']['rule_number'],
                }

        if verbose:
            print(f"\nExpanded to {len(parent_results)} parent chunks")

        # Step 4: Re-rank parent chunks with cross-encoder
        if parent_results:
            pairs = [[query, parent_results[pid]['chunk']['text']] for pid in parent_results.keys()]
            rerank_scores = self.reranker.predict(pairs)

            # Normalize rerank scores
            rerank_min = rerank_scores.min()
            rerank_max = rerank_scores.max()
            if rerank_max > rerank_min:
                rerank_normalized = (rerank_scores - rerank_min) / (rerank_max - rerank_min)
            else:
                rerank_normalized = np.ones_like(rerank_scores)

            # Add re-rank scores
            for i, parent_id in enumerate(parent_results.keys()):
                parent_results[parent_id]['rerank_score'] = float(rerank_normalized[i])

        # Step 5: Sort by re-rank score and return
        final_results = []
        for parent_id, data in sorted(
            parent_results.items(),
            key=lambda x: x[1].get('rerank_score', 0),
            reverse=True
        )[:top_k_parents]:
            parent = data['chunk']
            final_results.append({
                'chunk_id': parent['id'],
                'rule_number': parent['metadata']['rule_number'],
                'rule_title': parent['metadata']['rule_title'],
                'text': parent['text'],
                'num_children': parent['metadata']['num_children'],
                'rerank_score': data.get('rerank_score', 0),
                'citation': f"Rule {parent['metadata']['rule_number']} ({parent['metadata']['rule_title']})",
            })

        if verbose:
            print(f"\nFinal ranked results (after cross-encoder re-ranking):")
            for i, r in enumerate(final_results, 1):
                print(f"  {i}. Rule {r['rule_number']}: {r['rerank_score']:.3f}")

        return final_results


def test_parent_child():
    """Test parent-child retrieval."""
    print()
    print("=" * 80)
    print("PARENT-CHILD RETRIEVAL TEST")
    print("=" * 80)
    print()

    retrieval = ParentChildRetrieval()
    retrieval.setup()

    print()
    print("Testing on key questions:")
    print()

    test_queries = [
        "What actions constitute a traveling violation?",
        "When is defensive goaltending called?",
        "What are the rules for fouls?",
        "How many timeouts per game?",
    ]

    for query in test_queries:
        print(f"Q: {query}")
        print("-" * 80)
        results = retrieval.retrieve_parent_child(query, top_k_parents=3, verbose=True)
        print()


if __name__ == "__main__":
    test_parent_child()
