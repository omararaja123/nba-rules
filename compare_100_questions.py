"""
Compare Hybrid vs Super Chunks on 100 diverse questions.
Quick evaluation without API calls - checks if correct rule mentioned.
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import faiss

print("=" * 80)
print("LOADING DATA FOR 100-QUESTION COMPARISON")
print("=" * 80)
print()

# Load test questions
with open('data/100_test_questions.json', 'r') as f:
    test_questions = json.load(f)

print(f"✅ Loaded {len(test_questions)} test questions")
print()

# Load model
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model loaded")
print()

def test_approach(chunks_file: str, embeddings_file: str, approach_name: str):
    """Test an approach on all 100 questions."""

    print()
    print("=" * 80)
    print(f"TESTING: {approach_name}")
    print("=" * 80)
    print()

    # Load chunks
    with open(chunks_file, 'r') as f:
        data = json.load(f)
    chunks = data['chunks']

    print(f"Loaded {len(chunks)} chunks")

    # Load embeddings
    embeddings = np.load(embeddings_file)
    print(f"Loaded embeddings: {embeddings.shape}")

    # Build FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings.astype(np.float32))

    # Build BM25
    texts = [c['text'] for c in chunks]
    tokenized = [text.lower().split() for text in texts]
    bm25 = BM25Okapi(tokenized)

    print("✅ Retrieval system ready")
    print()

    results = []
    correct = 0

    print("Testing questions...")
    print()

    for i, q in enumerate(test_questions, 1):
        question = q['question']
        expected_rule = q['rule']

        # Encode query
        query_embedding = model.encode(question)

        # Semantic search
        distances, indices = index.search(
            np.array([query_embedding]).astype(np.float32), 10
        )

        # BM25 search
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

            if rule not in retrieved_rules or retrieved_rules[rule] < combined:
                retrieved_rules[rule] = combined

        # Check if expected rule in top results
        top_rules = sorted(retrieved_rules.items(), key=lambda x: x[1], reverse=True)
        top_rule = top_rules[0][0] if top_rules else None
        found = top_rule == expected_rule

        if found:
            correct += 1

        results.append({
            'id': q['id'],
            'question': question,
            'expected_rule': expected_rule,
            'retrieved_rule': top_rule,
            'correct': found,
        })

        if i % 20 == 0:
            print(f"  [{i}/100] Processed {i} questions (Accuracy: {(correct/i)*100:.1f}%)")

    accuracy = (correct / len(test_questions)) * 100

    print()
    print("=" * 80)
    print(f"RESULTS: {approach_name}")
    print("=" * 80)
    print()
    print(f"Accuracy: {correct}/100 ({accuracy:.1f}%)")
    print()

    # Show failures
    failures = [r for r in results if not r['correct']]
    if failures:
        print(f"Failed questions ({len(failures)}):")
        for f in failures[:5]:
            print(f"  Q{f['id']}: Expected Rule {f['expected_rule']}, got Rule {f['retrieved_rule']}")
            print(f"    '{f['question'][:60]}...'")
        if len(failures) > 5:
            print(f"  ... and {len(failures) - 5} more")
        print()

    return accuracy, results


# Test both approaches
print()
hybrid_accuracy, hybrid_results = test_approach(
    'data/09_stable_chunks.json',
    'data/10_embeddings.npy',
    'HYBRID RETRIEVAL (Original Chunks)'
)

superchunk_accuracy, superchunk_results = test_approach(
    'data/09_stable_chunks_with_superchunks.json',
    'data/10_embeddings_with_superchunks.npy',
    'SUPER CHUNKS RETRIEVAL'
)

# Final comparison
print()
print("=" * 80)
print("FINAL COMPARISON: 100 DIVERSE QUESTIONS")
print("=" * 80)
print()

print(f"{'Approach':<30} {'Accuracy':<15} {'Improvement'}")
print("-" * 80)
print(f"{'Hybrid Retrieval':<30} {hybrid_accuracy:>6.1f}%{'':<7}")
print(f"{'Super Chunks':<30} {superchunk_accuracy:>6.1f}%{'':<7} +{superchunk_accuracy - hybrid_accuracy:.1f}%")
print()

# Detailed breakdown by rule
print("Accuracy by Rule:")
print()
print(f"{'Rule':<8} {'Questions':<15} {'Hybrid':<15} {'SuperChunks':<15} {'Difference'}")
print("-" * 80)

rule_stats = {}
for r in test_questions:
    rule = r['rule']
    if rule not in rule_stats:
        rule_stats[rule] = {'total': 0, 'hybrid_correct': 0, 'super_correct': 0}
    rule_stats[rule]['total'] += 1

for r in hybrid_results:
    if r['correct']:
        rule_stats[r['expected_rule']]['hybrid_correct'] += 1

for r in superchunk_results:
    if r['correct']:
        rule_stats[r['expected_rule']]['super_correct'] += 1

for rule in sorted(rule_stats.keys()):
    stats = rule_stats[rule]
    hybrid_pct = (stats['hybrid_correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
    super_pct = (stats['super_correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
    diff = super_pct - hybrid_pct

    print(f"{rule:<8} {stats['total']:<15} {hybrid_pct:>6.1f}%{'':<7} {super_pct:>6.1f}%{'':<7} {diff:+.1f}%")

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()

if superchunk_accuracy > hybrid_accuracy:
    improvement = superchunk_accuracy - hybrid_accuracy
    print(f"✅ Super Chunks outperforms Hybrid by {improvement:.1f}%")
    print(f"   Super Chunks: {superchunk_accuracy:.1f}% (Recommended for final solution)")
    print(f"   Hybrid: {hybrid_accuracy:.1f}%")
elif hybrid_accuracy > superchunk_accuracy:
    print(f"✅ Hybrid performs better by {hybrid_accuracy - superchunk_accuracy:.1f}%")
else:
    print(f"✅ Both approaches perform equally at {hybrid_accuracy:.1f}%")

print()
