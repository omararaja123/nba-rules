"""
Phase 3: Embeddings for NBA Rules RAG
Generate semantic embeddings and build vector retrieval system.

Pipeline:
1. Load chunks from stable JSON
2. Generate embeddings using SentenceTransformers
3. Store embeddings with metadata in FAISS
4. Test retrieval with sample questions
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')


class EmbeddingPipeline:
    """Generate embeddings and manage vector retrieval."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        """
        Initialize embedding pipeline.

        Args:
            model_name: Hugging Face model ID (default: all-MiniLM-L6-v2)
            device: 'cpu' or 'cuda' (default: cpu for compatibility)
        """
        self.model_name = model_name
        self.device = device

        print("=" * 80)
        print("PHASE 3: EMBEDDINGS & VECTOR RETRIEVAL")
        print("=" * 80)
        print()

        print("Loading embedding model...")
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name, device=device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()

            print(f"✅ Model loaded: {model_name}")
            print(f"   Dimension: {self.embedding_dim}")
            print(f"   Device: {device}")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print("   Install with: pip install sentence-transformers")
            raise

        print()

        # Storage for embeddings and metadata
        self.chunks = []
        self.embeddings = []
        self.metadata = []
        self.chunk_index = {}  # Map chunk_id to index

    def load_chunks(self, chunks_path: str) -> int:
        """
        Load chunks from stable JSON file.

        Args:
            chunks_path: Path to 09_stable_chunks.json

        Returns:
            Number of chunks loaded
        """
        print(f"Loading chunks from {chunks_path}...")

        try:
            with open(chunks_path, encoding='utf-8') as f:
                data = json.load(f)

            chunks = data.get('chunks', [])

            if not chunks:
                raise ValueError("No chunks found in JSON")

            print(f"✅ Loaded {len(chunks)} chunks")
            print()

            # Validate chunks
            valid_count = 0
            skipped = []

            for i, chunk in enumerate(chunks):
                try:
                    # Validate required fields
                    if not chunk.get('text') or not chunk.get('text').strip():
                        skipped.append((chunk.get('id', 'unknown'), "empty text"))
                        continue

                    if not chunk.get('id'):
                        skipped.append(('unknown', "missing chunk_id"))
                        continue

                    if not chunk.get('metadata'):
                        skipped.append((chunk.get('id'), "missing metadata"))
                        continue

                    # Store valid chunk
                    self.chunks.append(chunk)
                    self.chunk_index[chunk['id']] = len(self.chunks) - 1
                    valid_count += 1

                except Exception as e:
                    skipped.append((chunk.get('id', 'unknown'), str(e)))

            if skipped:
                print(f"⚠️  Skipped {len(skipped)} chunks:")
                for chunk_id, reason in skipped[:5]:
                    print(f"   - {chunk_id}: {reason}")
                if len(skipped) > 5:
                    print(f"   ... and {len(skipped) - 5} more")
                print()

            print(f"✅ Valid chunks: {valid_count}/{len(chunks)}")
            print()

            return valid_count

        except FileNotFoundError:
            print(f"❌ File not found: {chunks_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            raise
        except Exception as e:
            print(f"❌ Error loading chunks: {e}")
            raise

    def generate_embeddings(self, batch_size: int = 32, show_progress: bool = True) -> int:
        """
        Generate embeddings for all chunks.

        Args:
            batch_size: Batch size for embedding generation
            show_progress: Whether to show progress

        Returns:
            Number of embeddings generated
        """
        print("Generating embeddings...")
        print(f"  Batch size: {batch_size}")
        print()

        try:
            texts = [chunk['text'] for chunk in self.chunks]

            # Generate embeddings
            self.embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_tensor=False,
                convert_to_numpy=True,
            )

            # Extract metadata
            self.metadata = [chunk['metadata'] for chunk in self.chunks]

            print()
            print(f"✅ Generated {len(self.embeddings)} embeddings")
            print(f"   Shape: {self.embeddings.shape}")
            print(f"   Dimensions: {self.embeddings.shape[1]}")
            print()

            return len(self.embeddings)

        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            raise

    def save_embeddings(self, output_dir: str = "data") -> None:
        """
        Save embeddings and metadata locally.

        Args:
            output_dir: Directory to save files
        """
        print("Saving embeddings...")

        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        try:
            # Save embeddings as numpy
            embeddings_file = output_dir / "10_embeddings.npy"
            np.save(embeddings_file, self.embeddings)
            print(f"✅ Saved embeddings: {embeddings_file}")

            # Save metadata as JSON
            metadata_file = output_dir / "10_embeddings_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        'total_embeddings': len(self.metadata),
                        'embedding_dimension': self.embeddings.shape[1],
                        'model': self.model_name,
                        'metadata': self.metadata,
                    },
                    f,
                    indent=2,
                )
            print(f"✅ Saved metadata: {metadata_file}")

            # Save chunk ID mappings
            id_map_file = output_dir / "10_chunk_id_map.json"
            with open(id_map_file, 'w', encoding='utf-8') as f:
                json.dump(self.chunk_index, f, indent=2)
            print(f"✅ Saved ID map: {id_map_file}")

            print()

        except Exception as e:
            print(f"❌ Error saving embeddings: {e}")
            raise

    def build_faiss_index(self) -> 'faiss.Index':
        """
        Build FAISS vector index for similarity search.

        Returns:
            FAISS index object
        """
        print("Building FAISS vector index...")

        try:
            import faiss

            # Validate embeddings
            if self.embeddings is None:
                raise ValueError("Embeddings not set. Call generate_embeddings() first.")

            if len(self.embeddings) == 0:
                raise ValueError("Embeddings array is empty.")

            # Create FAISS index
            embedding_array = np.array(self.embeddings, dtype=np.float32)

            # Ensure 2D shape
            if embedding_array.ndim != 2:
                raise ValueError(
                    f"Embeddings must be 2D (num_vectors, embedding_dim), "
                    f"got shape: {embedding_array.shape}"
                )

            num_vectors, embedding_dim = embedding_array.shape

            # Use simple L2 distance
            index = faiss.IndexFlatL2(embedding_dim)
            index.add(embedding_array)

            print(f"✅ FAISS index created")
            print(f"   Vectors: {index.ntotal}")
            print(f"   Dimension: {embedding_dim}")
            print()

            return index

        except ImportError:
            print("❌ FAISS not installed")
            print("   Install with: pip install faiss-cpu")
            raise
        except Exception as e:
            print(f"❌ Error building FAISS index: {e}")
            raise

    def similarity_search(
        self,
        query: str,
        index: 'faiss.Index',
        k: int = 3,
    ) -> List[Dict]:
        """
        Search for similar chunks.

        Args:
            query: Query text
            index: FAISS index
            k: Number of results to return

        Returns:
            List of retrieved chunks with scores
        """
        try:
            # Encode query
            query_embedding = self.model.encode(query, convert_to_tensor=False)
            query_embedding = np.array([query_embedding], dtype=np.float32)

            # Search
            distances, indices = index.search(query_embedding, k)

            # Format results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                # Convert to int to avoid numpy comparison issues
                idx = int(idx)
                dist = float(dist)

                if idx < 0:  # Invalid result
                    continue

                chunk = self.chunks[idx]
                metadata = self.metadata[idx]

                results.append({
                    'chunk_id': chunk['id'],
                    'rule_number': metadata['rule_number'],
                    'rule_title': metadata['rule_title'],
                    'section_number': metadata['section_number'],
                    'section_title': metadata['section_title'],
                    'page_number': metadata['page_number'],
                    'similarity_score': 1 / (1 + dist),  # Convert L2 distance to similarity
                    'text_preview': chunk['text'][:150],
                })

            return results

        except Exception as e:
            print(f"❌ Error during search: {e}")
            return []


def main():
    """Run complete embedding pipeline."""

    # Step 1: Initialize pipeline
    print()
    pipeline = EmbeddingPipeline(
        model_name="all-MiniLM-L6-v2",
        device="cpu"
    )

    # Step 2: Load chunks
    chunks_loaded = pipeline.load_chunks("data/09_stable_chunks.json")

    if chunks_loaded == 0:
        print("❌ No chunks loaded. Exiting.")
        return

    # Step 3: Generate embeddings
    embeddings_count = pipeline.generate_embeddings(batch_size=32, show_progress=True)

    # Step 4: Save embeddings
    pipeline.save_embeddings("data")

    # Step 5: Build FAISS index
    faiss_index = pipeline.build_faiss_index()

    # Step 6: Test retrieval with sample questions
    print("=" * 80)
    print("TESTING SIMILARITY SEARCH")
    print("=" * 80)
    print()

    test_questions = [
        "What actions constitute a traveling violation under NBA rules?",
        "When is defensive goaltending called?",
        "What behaviors can result in a technical foul?",
        "When does the shot clock reset to 14 seconds?",
        "What is the difference between Flagrant Foul Penalty 1 and Penalty 2?",
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"Question {i}: {question}")
        print("-" * 80)

        results = pipeline.similarity_search(question, faiss_index, k=3)

        if not results:
            print("❌ No results found")
            print()
            continue

        for j, result in enumerate(results, 1):
            print(f"  #{j} [Score: {result['similarity_score']:.3f}]")
            print(f"      Chunk ID: {result['chunk_id']}")
            print(f"      Rule {result['rule_number']}: {result['rule_title']}")
            print(f"      Section {result['section_number']}: {result['section_title']}")
            print(f"      Page: {result['page_number']}")
            print(f"      Text: {result['text_preview']}...")
            print()

    print("=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print()
    print("Embeddings saved to:")
    print("  - data/10_embeddings.npy (vector embeddings)")
    print("  - data/10_embeddings_metadata.json (metadata)")
    print("  - data/10_chunk_id_map.json (chunk ID index)")
    print()
    print("Ready for Phase 4: Retrieval System")
    print()


if __name__ == "__main__":
    main()
