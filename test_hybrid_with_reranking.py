"""
TEST: Hybrid Retrieval + Cross-Encoder Re-ranking
Compare: Current 76% (no reranking) vs With reranking
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import faiss

print("=" * 100)
print("TEST: HYBRID RETRIEVAL + CROSS-ENCODER RE-RANKING")
print("=" * 100)
print()

# Load chunks and embeddings
with open('data/09_stable_chunks_aggressive_rebuild.json', 'r') as f:
    data = json.load(f)
chunks = data['chunks']

embeddings = np.load('data/10_embeddings_aggressive_rebuild.npy')

# Setup
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings.astype(np.float32))

texts = [c['text'] for c in chunks]
tokenized = [text.lower().split() for text in texts]
bm25 = BM25Okapi(tokenized)
encoder = SentenceTransformer('all-MiniLM-L6-v2')

# Load cross-encoder for re-ranking
print("Loading cross-encoder...")
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
print("✅ Cross-encoder loaded")
print()

# Load test questions
with open('data/100_test_questions.json', 'r') as f:
    test_questions = json.load(f)

# Test both versions
print("=" * 100)
print("VERSION 1: WITHOUT RE-RANKING (Current - 76%)")
print("=" * 100)
print()

correct_without = 0
rule_accuracy_without = {}

for i, q in enumerate(test_questions, 1):
    question = q['question']
    expected_rule = q['rule']

    # Retrieve
    query_embedding = encoder.encode(question)
    distances, indices = index.search(np.array([query_embedding]).astype(np.float32), 10)

    tokens = question.lower().split()
    bm25_scores = bm25.get_scores(tokens)

    # Combine (no reranking)
    retrieved_rules = {}
    for j, idx in enumerate(indices[0]):
        chunk = chunks[idx]
        rule = chunk['metadata']['rule_number']

        sim_score = 1.0 / (1.0 + distances[0][j])
        bm25_score = min(1.0, bm25_scores[idx] / 10.0)
        combined = (sim_score * 0.7) + (bm25_score * 0.3)

        if rule not in retrieved_rules or retrieved_rules[rule] < combined:
            retrieved_rules[rule] = combined

    # Get top-3
    top3_rules = sorted(retrieved_rules.items(), key=lambda x: x[1], reverse=True)[:3]
    top3_list = [r[0] for r in top3_rules]

    is_correct = expected_rule in top3_list
    if is_correct:
        correct_without += 1

    if expected_rule not in rule_accuracy_without:
        rule_accuracy_without[expected_rule] = {'correct': 0, 'total': 0}
    rule_accuracy_without[expected_rule]['total'] += 1
    if is_correct:
        rule_accuracy_without[expected_rule]['correct'] += 1

    if i % 25 == 0:
        acc = (correct_without / i) * 100
        print(f"  [{i:3d}/100] Accuracy: {acc:.1f}%")

accuracy_without = (correct_without / len(test_questions)) * 100
print(f"\nResult: {correct_without}/100 ({accuracy_without:.1f}%)")
print()

# Test WITH re-ranking
print("=" * 100)
print("VERSION 2: WITH CROSS-ENCODER RE-RANKING (Testing)")
print("=" * 100)
print()

correct_with = 0
rule_accuracy_with = {}

for i, q in enumerate(test_questions, 1):
    question = q['question']
    expected_rule = q['rule']

    # Retrieve
    query_embedding = encoder.encode(question)
    distances, indices = index.search(np.array([query_embedding]).astype(np.float32), 10)

    tokens = question.lower().split()
    bm25_scores = bm25.get_scores(tokens)

    # Combine scores with ALL chunks
    chunk_scores = []
    for j, idx in enumerate(indices[0]):
        chunk = chunks[idx]
        rule = chunk['metadata']['rule_number']

        sim_score = 1.0 / (1.0 + distances[0][j])
        bm25_score = min(1.0, bm25_scores[idx] / 10.0)
        combined = (sim_score * 0.7) + (bm25_score * 0.3)

        chunk_scores.append((idx, rule, combined, chunk['text']))

    # Re-rank with cross-encoder
    rerank_pairs = [[question, chunk_text] for _, _, _, chunk_text in chunk_scores]
    rerank_scores = reranker.predict(rerank_pairs)

    # Combine hybrid score (60%) + rerank score (40%)
    combined_scores = []
    for j, (idx, rule, hybrid_score, _) in enumerate(chunk_scores):
        # Normalize rerank score to 0-1
        rerank_norm = (rerank_scores[j] + 3) / 6  # MARCO scores -3 to +3
        rerank_norm = max(0, min(1, rerank_norm))

        # Combine
        final_score = (hybrid_score * 0.6) + (rerank_norm * 0.4)
        combined_scores.append((rule, final_score))

    # Get top-3 rules
    retrieved_rules = {}
    for rule, score in combined_scores:
        if rule not in retrieved_rules or retrieved_rules[rule] < score:
            retrieved_rules[rule] = score

    top3_rules = sorted(retrieved_rules.items(), key=lambda x: x[1], reverse=True)[:3]
    top3_list = [r[0] for r in top3_rules]

    is_correct = expected_rule in top3_list
    if is_correct:
        correct_with += 1

    if expected_rule not in rule_accuracy_with:
        rule_accuracy_with[expected_rule] = {'correct': 0, 'total': 0}
    rule_accuracy_with[expected_rule]['total'] += 1
    if is_correct:
        rule_accuracy_with[expected_rule]['correct'] += 1

    if i % 25 == 0:
        acc = (correct_with / i) * 100
        print(f"  [{i:3d}/100] Accuracy: {acc:.1f}%")

accuracy_with = (correct_with / len(test_questions)) * 100
print(f"\nResult: {correct_with}/100 ({accuracy_with:.1f}%)")
print()

# Compare
print("=" * 100)
print("COMPARISON")
print("=" * 100)
print()

print(f"WITHOUT Re-ranking: {accuracy_without:.1f}% ({correct_without}/100)")
print(f"WITH Re-ranking:    {accuracy_with:.1f}% ({correct_with}/100)")
print(f"Difference:         {accuracy_with - accuracy_without:+.1f}%")
print()

if accuracy_with > accuracy_without:
    print(f"✅ RE-RANKING IMPROVED: +{accuracy_with - accuracy_without:.1f}%")
    print(f"   Recommendation: Use re-ranking version (76% → {accuracy_with:.1f}%)")
elif accuracy_with < accuracy_without:
    print(f"❌ RE-RANKING HURT: {accuracy_with - accuracy_without:.1f}%")
    print(f"   Recommendation: Stick with current version (76%)")
else:
    print(f"➖ NO DIFFERENCE: Same accuracy ({accuracy_without:.1f}%)")
    print(f"   Recommendation: Either works, current is faster")

print()

# Rule-by-rule comparison
print("=" * 100)
print("RULE-BY-RULE COMPARISON")
print("=" * 100)
print()

print(f"{'Rule':<8} {'Without':<12} {'With':<12} {'Difference':<15}")
print("-" * 50)

improved = 0
regressed = 0

for rule in sorted(rule_accuracy_without.keys()):
    stats_without = rule_accuracy_without[rule]
    stats_with = rule_accuracy_with[rule]

    acc_without = (stats_without['correct'] / stats_without['total']) * 100 if stats_without['total'] > 0 else 0
    acc_with = (stats_with['correct'] / stats_with['total']) * 100 if stats_with['total'] > 0 else 0

    diff = acc_with - acc_without

    if diff > 0:
        improved += 1
        marker = "↑"
    elif diff < 0:
        regressed += 1
        marker = "↓"
    else:
        marker = "→"

    print(f"{rule:<8} {acc_without:>6.1f}%{'':<5} {acc_with:>6.1f}%{'':<5} {diff:+.1f}% {marker}")

print()
print(f"Improved: {improved} rules | Regressed: {regressed} rules")
print()

