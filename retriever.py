"""
Retrieval module for NBA Rules RAG system
Handles document retrieval using hybrid search (semantic + keyword)
"""

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from config import (
    CHUNKS_FILE,
    EMBEDDINGS_FILE,
    TOP_K_RETRIEVAL,
    SEMANTIC_WEIGHT,
    KEYWORD_WEIGHT,
    RERANKER_WEIGHT,
    HYBRID_WEIGHT,
    EMBEDDING_MODEL,
)


class NBARetriever:
    """Retrieves relevant NBA rule chunks using hybrid search strategy."""

    def __init__(self):
        """Initialize the retriever with chunks and embeddings."""
        self.chunks = None
        self.embeddings = None
        self.index = None
        self.bm25 = None
        self.encoder = None
        self.reranker = None

        self._load_data()
        self._setup_retrieval()

    def _load_data(self):
        """Load chunks and embeddings from disk."""
        # Load chunks
        with open(CHUNKS_FILE, 'r') as f:
            data = json.load(f)
            self.chunks = data['chunks']

        # Load embeddings
        self.embeddings = np.load(EMBEDDINGS_FILE)

    def _setup_retrieval(self):
        """Set up retrieval indices and models."""
        # FAISS index for semantic search
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings.astype(np.float32))

        # BM25 for keyword search
        texts = [c['text'] for c in self.chunks]
        tokenized = [text.lower().split() for text in texts]
        self.bm25 = BM25Okapi(tokenized)

        # Load embedding model
        self.encoder = SentenceTransformer(EMBEDDING_MODEL)

        # Load re-ranker model
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def retrieve(self, query: str) -> list:
        """
        Retrieve relevant chunks for a query using hybrid search.

        Args:
            query: User question

        Returns:
            List of dicts with chunk info, relevance scores, and metadata
        """
        # Encode query
        query_embedding = self.encoder.encode(query)

        # Semantic search (FAISS)
        distances, indices = self.index.search(
            np.array([query_embedding]).astype(np.float32),
            10
        )

        # Keyword search (BM25)
        tokens = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokens)

        # Combine scores for all retrieved chunks
        chunk_scores = []
        for j, idx in enumerate(indices[0]):
            chunk = self.chunks[idx]

            # Semantic similarity score
            semantic_score = 1.0 / (1.0 + distances[0][j])

            # BM25 keyword score (normalized)
            keyword_score = min(1.0, bm25_scores[idx] / 10.0)

            # Hybrid score
            hybrid_score = (semantic_score * SEMANTIC_WEIGHT +
                          keyword_score * KEYWORD_WEIGHT)

            chunk_scores.append({
                'idx': idx,
                'rule': chunk['metadata']['rule_number'],
                'hybrid_score': hybrid_score,
                'semantic_score': semantic_score,
                'keyword_score': keyword_score,
                'text': chunk['text'],
                'metadata': chunk['metadata']
            })

        # Apply cross-encoder re-ranking
        rerank_pairs = [[query, c['text']] for c in chunk_scores]
        rerank_scores = self.reranker.predict(rerank_pairs)

        # Combine hybrid and re-ranking scores
        final_scores = []
        for j, c in enumerate(chunk_scores):
            rerank_norm = (rerank_scores[j] + 3) / 6  # Normalize to 0-1
            rerank_norm = max(0, min(1, rerank_norm))

            final_score = (c['hybrid_score'] * HYBRID_WEIGHT +
                         rerank_norm * RERANKER_WEIGHT)

            final_scores.append({
                'rule_number': c['rule'],
                'rule_title': c['metadata'].get('rule_title', 'Unknown'),
                'section_title': c['metadata'].get('section_title', ''),
                'page_number': c['metadata'].get('page_number', 'Unknown'),
                'chunk_id': c['metadata'].get('chunk_id', ''),
                'text': c['text'],
                'relevance_score': final_score,
                'hybrid_score': c['hybrid_score'],
                'rerank_score': rerank_norm
            })

        # Sort by final score and return top-k
        final_scores.sort(key=lambda x: x['relevance_score'], reverse=True)
        return final_scores[:TOP_K_RETRIEVAL]

    def format_context(self, retrieved_chunks: list) -> str:
        """
        Format retrieved chunks into a context string for the LLM.

        Args:
            retrieved_chunks: List of retrieved chunk dicts

        Returns:
            Formatted context string
        """
        if not retrieved_chunks:
            return "No relevant rules found."

        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            context_parts.append(
                f"[Source {i}] Rule {chunk['rule_number']}: {chunk['rule_title']}\n"
                f"Section: {chunk['section_title']}\n"
                f"Page: {chunk['page_number']}\n"
                f"\n{chunk['text']}\n"
            )

        return "\n---\n".join(context_parts)

    def get_citation_info(self, retrieved_chunks: list) -> dict:
        """
        Get citation information from retrieved chunks.

        Args:
            retrieved_chunks: List of retrieved chunk dicts

        Returns:
            Dict mapping chunk index to citation info
        """
        citations = {}
        for i, chunk in enumerate(retrieved_chunks, 1):
            citations[i] = {
                'rule': chunk['rule_number'],
                'title': chunk['rule_title'],
                'section': chunk['section_title'],
                'page': chunk['page_number']
            }
        return citations
