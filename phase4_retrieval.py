"""
Phase 4: Retrieval Pipeline
Vector similarity search and chunk retrieval.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent))

from phase3_embeddings import EmbeddingPipeline


class RetrievalPipeline:
    """Search and retrieve chunks from vector database."""

    def __init__(self):
        """Initialize retrieval pipeline."""
        self.pipeline = EmbeddingPipeline()
        self.faiss_index = None
        self.chunks = []
        self.metadata = []
        self.embeddings = None

    def setup(self):
        """Load embeddings and build index."""
        print("=" * 80)
        print("PHASE 4: RETRIEVAL & GENERATION")
        print("=" * 80)
        print()

        print("Setting up retrieval pipeline...")

        # Load chunks
        self.pipeline.load_chunks("data/09_stable_chunks.json")
        self.chunks = self.pipeline.chunks

        # Load pre-generated embeddings
        embeddings_file = Path("data/10_embeddings.npy")
        if not embeddings_file.exists():
            print("❌ Embeddings not found. Generating...")
            self.pipeline.generate_embeddings(batch_size=32, show_progress=False)
        else:
            print(f"✅ Loading pre-generated embeddings from {embeddings_file}")
            loaded_embeddings = np.load(embeddings_file)
            # Set embeddings in pipeline so FAISS can access them
            self.pipeline.embeddings = loaded_embeddings

        self.embeddings = self.pipeline.embeddings
        self.metadata = self.pipeline.metadata

        # Verify embeddings shape
        if self.embeddings is None or len(self.embeddings) == 0:
            print("❌ No embeddings loaded or generated")
            return False

        print(f"✅ Embeddings shape: {self.embeddings.shape}")

        # Verify chunks and metadata alignment
        if len(self.chunks) != len(self.metadata):
            print(f"⚠️  Warning: {len(self.chunks)} chunks but {len(self.metadata)} metadata entries")
            # Try to fix by regenerating metadata
            self.metadata = [c['metadata'] for c in self.chunks]
            print(f"✅ Regenerated metadata: {len(self.metadata)} entries")

        if len(self.chunks) != len(self.embeddings):
            print(f"❌ Mismatch: {len(self.chunks)} chunks, {len(self.embeddings)} embeddings")
            return False

        print(f"✅ Chunks, metadata, and embeddings aligned: {len(self.chunks)} items")

        # Build FAISS index
        self.faiss_index = self.pipeline.build_faiss_index()

        print()
        return True

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        verbose: bool = False,
    ) -> List[Dict]:
        """
        Retrieve top-k chunks for a query.

        Args:
            query: User question
            top_k: Number of chunks to retrieve (default: 5)
            verbose: Print retrieval details

        Returns:
            List of retrieved chunks with metadata and similarity scores
        """
        try:
            # Encode query
            query_embedding = self.pipeline.model.encode(
                query,
                convert_to_tensor=False
            )
            query_embedding = np.array([query_embedding], dtype=np.float32)

            # Search FAISS index
            distances, indices = self.faiss_index.search(query_embedding, top_k)

            # Format results
            results = []
            for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
                idx = int(idx)
                dist = float(dist)

                if idx < 0 or idx >= len(self.chunks):  # Invalid result
                    if verbose:
                        print(f"  ⚠️  Skipped invalid index {idx}")
                    continue

                chunk = self.chunks[idx]
                metadata = self.metadata[idx]

                # Convert L2 distance to similarity score (0-1)
                similarity_score = 1 / (1 + dist)

                result = {
                    # Chunk identification
                    "chunk_id": chunk['id'],
                    "rank": rank,
                    "similarity_score": similarity_score,

                    # Content
                    "text": chunk['text'],

                    # Metadata (for citations)
                    "rule_number": metadata['rule_number'],
                    "rule_title": metadata['rule_title'],
                    "section_number": metadata['section_number'],
                    "section_title": metadata['section_title'],
                    "page_number": metadata['page_number'],
                    "token_count": metadata['token_count'],

                    # Citation string
                    "citation": (
                        f"Rule {metadata['rule_number']}, Section {metadata['section_number']} "
                        f"({metadata['section_title']}), p. {metadata['page_number']}"
                    ),
                }

                results.append(result)

                if verbose:
                    print(
                        f"  #{rank} [Score: {similarity_score:.3f}] {result['citation']}"
                    )

            return results

        except Exception as e:
            print(f"❌ Retrieval error: {e}")
            return []

    def format_context(self, retrieved_chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into LLM context.

        Args:
            retrieved_chunks: List of retrieved chunks

        Returns:
            Formatted context string
        """
        if not retrieved_chunks:
            return "No relevant NBA rules sections were found for this query."

        context = "Retrieved NBA Rules Excerpts:\n"
        context += "=" * 80 + "\n\n"

        for i, chunk in enumerate(retrieved_chunks, 1):
            context += f"[{i}] {chunk['citation']}\n"
            context += f"Relevance Score: {chunk['similarity_score']:.2%}\n"
            context += "-" * 80 + "\n"
            context += chunk['text']
            context += "\n\n"

        return context

    def get_citation_metadata(self, retrieved_chunks: List[Dict]) -> List[Dict]:
        """
        Extract citation metadata from retrieved chunks.

        Args:
            retrieved_chunks: List of retrieved chunks

        Returns:
            List of citation dictionaries
        """
        return [
            {
                "chunk_id": chunk['chunk_id'],
                "citation": chunk['citation'],
                "rule_number": chunk['rule_number'],
                "section_title": chunk['section_title'],
                "page_number": chunk['page_number'],
                "similarity_score": chunk['similarity_score'],
            }
            for chunk in retrieved_chunks
        ]


def main():
    """Test retrieval pipeline."""
    pipeline = RetrievalPipeline()
    pipeline.setup()

    print()
    print("=" * 80)
    print("TESTING RETRIEVAL")
    print("=" * 80)
    print()

    test_questions = [
        "What is traveling?",
        "When is a technical foul called?",
        "How many timeouts per game?",
    ]

    for question in test_questions:
        print(f"Q: {question}")
        print("-" * 80)

        results = pipeline.retrieve(question, top_k=3, verbose=True)
        context = pipeline.format_context(results)

        print(f"\nFormatted context length: {len(context)} chars")
        print()


if __name__ == "__main__":
    main()
