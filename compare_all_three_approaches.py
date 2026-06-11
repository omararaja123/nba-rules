"""
Compare all three approaches on 100 questions:
1. Pure Hybrid
2. Super Chunks
3. Parent-Child with Cross-Encoder
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import faiss

print("=" * 80)
print("COMPREHENSIVE 3-WAY COMPARISON: 100 QUESTIONS")
print("=" * 80)
print()

# Load test questions
with open('data/100_test_questions.json', 'r') as f:
    test_questions = json.load(f)

print(f"Testing {len(test_questions)} questions across 3 approaches")
print()

# Load encoder once
print("Loading models...")
encoder = SentenceTransformer('all-MiniLM-L6-v2')
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
print("✅ Models loaded")
print()

def test_approach_3way(chunks_file: str, embeddings_file: str, use_reranking: bool, name: str):
    """Test an approach."""

    print()
    print("=" * 80)
    print(f"TESTING: {name}")
    print("=" * 80)
    print()

    # Load data
    with open(chunks_file, 'r') as f:
        data = json.load(f)
    chunks = data['chunks']

    embeddings = np.load(embeddings_file)

    # Build index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings.astype(np.float32))

    # Build BM25
    texts = [c['text'] for c in chunks]
    tokenized = [text.lower().split() for text in texts]
    bm25 = BM25Okapi(tokenized)

    print(f"Chunks: {len(chunks)}, Embeddings: {embeddings.shape}")
    print()

    correct = 0

    for i, q in enumerate(test_questions, 1):
        question = q['question']
        expected_rule = q['rule']

        # Retrieve
        query_embedding = encoder.encode(question)
        distances, indices = index.search(
            np.array([query_embedding]).astype(np.float32), 10
        )

        # BM25
        tokens = question.lower().split()
        bm25_scores = bm25.get_scores(tokens)

        # Combine
        retrieved_rules = {}
        for j, idx in enumerate(indices[0]):
            chunk = chunks[idx]
            rule = chunk['metadata']['rule_number']

            sim_score = 1.0 / (1.0 + distances[0][j])
            bm25_score = min(1.0, bm25_scores[idx] / 10.0)
            combined = (sim_score * 0.7) + (bm25_score * 0.3)

            if use_reranking:
                # Re-rank with cross-encoder
                rerank_scores = reranker.predict([[question, chunk['text']]])
                rerank_score = float(rerank_scores[0]) if isinstance(rerank_scores, np.ndarray) else float(rerank_scores)
                # Normalize to 0-1
                rerank_norm = (rerank_score + 3) / 6  # MARCO scores are -3 to +3
                rerank_norm = max(0, min(1, rerank_norm))
                combined = combined * 0.5 + rerank_norm * 0.5

            if rule not in retrieved_rules or retrieved_rules[rule] < combined:
                retrieved_rules[rule] = combined

        # Get top rule
        top_rule = max(retrieved_rules.items(), key=lambda x: x[1])[0] if retrieved_rules else None

        if top_rule == expected_rule:
            correct += 1

        if i % 25 == 0:
            accuracy = (correct / i) * 100
            print(f"  [{i:3d}/100] Accuracy: {accuracy:.1f}%")

    accuracy = (correct / len(test_questions)) * 100
    print()
    print(f"FINAL: {correct}/100 ({accuracy:.1f}%)")
    print()

    return accuracy


# Test all three
print("Starting tests (this will take 5-10 minutes)...")
print()

hybrid_acc = test_approach_3way(
    'data/09_stable_chunks.json',
    'data/10_embeddings.npy',
    False,
    'HYBRID (Semantic + BM25)'
)

superchunk_acc = test_approach_3way(
    'data/09_stable_chunks_with_superchunks.json',
    'data/10_embeddings_with_superchunks.npy',
    False,
    'SUPER CHUNKS (No Re-ranking)'
)

parentchild_acc = test_approach_3way(
    'data/11_parent_chunks.json',
    'data/11_parent_embeddings.npy',
    True,
    'PARENT-CHILD (With Cross-Encoder Re-ranking)'
)

# Final comparison
print()
print("=" * 80)
print("FINAL RESULTS: ALL 3 APPROACHES ON 100 QUESTIONS")
print("=" * 80)
print()

results = [
    ('Hybrid Retrieval', hybrid_acc),
    ('Super Chunks', superchunk_acc),
    ('Parent-Child + Cross-Encoder', parentchild_acc),
]

results_sorted = sorted(results, key=lambda x: x[1], reverse=True)

print(f"{'Rank':<6} {'Approach':<35} {'Accuracy':<15} {'Improvement'}")
print("-" * 80)

for rank, (name, acc) in enumerate(results_sorted, 1):
    baseline = hybrid_acc
    improvement = acc - baseline
    improvement_str = f"+{improvement:.1f}%" if improvement > 0 else f"{improvement:.1f}%"
    print(f"{rank:<6} {name:<35} {acc:>6.1f}%{'':<7} {improvement_str:>10}")

print()
best_name = results_sorted[0][0]
best_acc = results_sorted[0][1]

print(f"🏆 WINNER: {best_name} ({best_acc:.1f}%)")
print()
