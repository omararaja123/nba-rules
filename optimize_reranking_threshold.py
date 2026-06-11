"""
OPTION B: Optimize Cross-Encoder Reranking Threshold
Test different weight combinations to find sweet spot
Goal: Keep gains (+3%) while minimizing regressions
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import faiss

print("=" * 100)
print("OPTIMIZING RERANKING THRESHOLD")
print("=" * 100)
print()

# Setup
with open('data/09_stable_chunks_aggressive_rebuild.json', 'r') as f:
    data = json.load(f)
chunks = data['chunks']

embeddings = np.load('data/10_embeddings_aggressive_rebuild.npy')

index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings.astype(np.float32))

texts = [c['text'] for c in chunks]
tokenized = [text.lower().split() for text in texts]
bm25 = BM25Okapi(tokenized)
encoder = SentenceTransformer('all-MiniLM-L6-v2')
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

with open('data/100_test_questions.json', 'r') as f:
    test_questions = json.load(f)

# Test different weights
weights_to_test = [
    ("No Reranking", 0.0),    # Baseline
    ("Light (0.2)", 0.2),     # Very light
    ("Moderate (0.3)", 0.3),  # Moderate
    ("Medium (0.35)", 0.35),  # Medium-high
    ("Full (0.4)", 0.4),      # What we had
]

results_by_weight = {}

for weight_name, rerank_weight in weights_to_test:
    print(f"Testing {weight_name}...")

    correct = 0
    rule_accuracy = {}

    for i, q in enumerate(test_questions, 1):
        question = q['question']
        expected_rule = q['rule']

        # Retrieve
        query_embedding = encoder.encode(question)
        distances, indices = index.search(np.array([query_embedding]).astype(np.float32), 10)

        tokens = question.lower().split()
        bm25_scores = bm25.get_scores(tokens)

        # Get scores for all chunks
        chunk_scores = []
        for j, idx in enumerate(indices[0]):
            chunk = chunks[idx]
            rule = chunk['metadata']['rule_number']

            sim_score = 1.0 / (1.0 + distances[0][j])
            bm25_score = min(1.0, bm25_scores[idx] / 10.0)
            hybrid_score = (sim_score * 0.7) + (bm25_score * 0.3)

            chunk_scores.append((idx, rule, hybrid_score, chunk['text']))

        # Apply reranking based on weight
        if rerank_weight > 0:
            rerank_pairs = [[question, chunk_text] for _, _, _, chunk_text in chunk_scores]
            rerank_scores = reranker.predict(rerank_pairs)

            combined_scores = []
            for j, (idx, rule, hybrid_score, _) in enumerate(chunk_scores):
                rerank_norm = (rerank_scores[j] + 3) / 6
                rerank_norm = max(0, min(1, rerank_norm))

                final_score = (hybrid_score * (1 - rerank_weight)) + (rerank_norm * rerank_weight)
                combined_scores.append((rule, final_score))
        else:
            # No reranking - just use hybrid scores
            combined_scores = [(rule, hybrid_score) for _, rule, hybrid_score, _ in chunk_scores]

        # Get top-3 rules
        retrieved_rules = {}
        for rule, score in combined_scores:
            if rule not in retrieved_rules or retrieved_rules[rule] < score:
                retrieved_rules[rule] = score

        top3_rules = sorted(retrieved_rules.items(), key=lambda x: x[1], reverse=True)[:3]
        top3_list = [r[0] for r in top3_rules]

        is_correct = expected_rule in top3_list
        if is_correct:
            correct += 1

        if expected_rule not in rule_accuracy:
            rule_accuracy[expected_rule] = {'correct': 0, 'total': 0}
        rule_accuracy[expected_rule]['total'] += 1
        if is_correct:
            rule_accuracy[expected_rule]['correct'] += 1

    accuracy = (correct / len(test_questions)) * 100
    results_by_weight[weight_name] = {
        'accuracy': accuracy,
        'correct': correct,
        'rule_accuracy': rule_accuracy
    }

    print(f"  Result: {correct}/100 ({accuracy:.1f}%)")
    print()

# Summary
print()
print("=" * 100)
print("SUMMARY: ALL WEIGHTS")
print("=" * 100)
print()

print(f"{'Weight':<20} {'Accuracy':<15} {'vs Baseline':<15} {'Status'}")
print("-" * 70)

baseline_acc = results_by_weight["No Reranking"]['accuracy']

for weight_name in weights_to_test:
    weight_name_display, _ = weight_name
    result = results_by_weight[weight_name_display]
    acc = result['accuracy']
    diff = acc - baseline_acc

    if diff > 0:
        status = f"+{diff:.1f}% ↑ BETTER"
    elif diff < 0:
        status = f"{diff:.1f}% ↓ WORSE"
    else:
        status = "BASELINE"

    print(f"{weight_name_display:<20} {acc:>6.1f}%{'':<8} {diff:+.1f}%{'':<10} {status}")

print()

# Find best
best_weight = max(results_by_weight.items(), key=lambda x: x[1]['accuracy'])
print(f"🏆 BEST: {best_weight[0]} ({best_weight[1]['accuracy']:.1f}%)")
print()

# Detailed comparison of best vs baseline
if best_weight[0] != "No Reranking":
    print("=" * 100)
    print(f"DETAILED COMPARISON: {best_weight[0]} vs BASELINE")
    print("=" * 100)
    print()

    baseline_rules = results_by_weight["No Reranking"]['rule_accuracy']
    best_rules = best_weight[1]['rule_accuracy']

    print(f"{'Rule':<8} {'Baseline':<15} {'Optimized':<15} {'Change':<15}")
    print("-" * 60)

    improved = 0
    regressed = 0

    for rule in sorted(baseline_rules.keys()):
        base_stats = baseline_rules[rule]
        best_stats = best_rules[rule]

        base_acc = (base_stats['correct'] / base_stats['total']) * 100 if base_stats['total'] > 0 else 0
        best_acc = (best_stats['correct'] / best_stats['total']) * 100 if best_stats['total'] > 0 else 0

        diff = best_acc - base_acc

        if diff > 0:
            improved += 1
            marker = "↑"
        elif diff < 0:
            regressed += 1
            marker = "↓"
        else:
            marker = "→"

        print(f"{rule:<8} {base_acc:>6.1f}%{'':<8} {best_acc:>6.1f}%{'':<8} {diff:+.1f}% {marker}")

    print()
    print(f"Improved: {improved} rules | Regressed: {regressed} rules | Net: {best_weight[1]['accuracy'] - baseline_acc:+.1f}%")
    print()

print("=" * 100)
print("RECOMMENDATION")
print("=" * 100)
print()

best_name, best_acc = best_weight[0], best_weight[1]['accuracy']
baseline = results_by_weight["No Reranking"]['accuracy']
improvement = best_acc - baseline

print(f"Best configuration: {best_name}")
print(f"Accuracy: {best_acc:.1f}% (vs {baseline:.1f}% baseline)")
print(f"Improvement: +{improvement:.1f}%")
print()

if improvement >= 2.0:
    print("✅ WORTH USING - Significant improvement with minimal regression")
elif improvement >= 0.5:
    print("✅ MIGHT BE WORTH USING - Small improvement, check rule regressions")
else:
    print("➖ NOT WORTH USING - No meaningful improvement")

print()

